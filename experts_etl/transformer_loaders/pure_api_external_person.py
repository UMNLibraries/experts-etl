from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import json
import uuid
from experts_dw import db
from sqlalchemy import and_, func
from experts_dw.models import PureApiExternalPerson, PureApiExternalPersonHst, Person, PureOrg, PersonPureOrg, PersonScopusId
from experts_etl import loggers
from pureapi import response

# defaults:

db_name = 'hotel'
transaction_record_limit = 100 
pure_api_record_logger = loggers.pure_api_record_logger(name='external_persons')
experts_etl_logger = loggers.experts_etl_logger()

def extract_api_persons(session):
  sq = session.query(
    PureApiExternalPerson.uuid,
    func.max(PureApiExternalPerson.modified).label('modified')
  ).select_from(PureApiExternalPerson).group_by(PureApiExternalPerson.uuid).subquery()

  for person in (session.query(PureApiExternalPerson)
    .join(
      sq,
      and_(PureApiExternalPerson.uuid==sq.c.uuid, PureApiExternalPerson.modified==sq.c.modified)
    )
    .all()
  ):
    yield person

def get_person_ids(api_person):
  person_ids = {
    'scopus_ids': set(),
  }
  if api_person.externalIdSource == 'Scopus':
    person_ids['scopus_ids'].add(api_person.externalId)
  return person_ids

def mark_api_persons_as_processed(session, pure_api_record_logger, processed_api_person_uuids):
  for uuid in processed_api_person_uuids:
    for person in session.query(PureApiExternalPerson).filter(PureApiExternalPerson.uuid==uuid).all():

      person_hst = (
        session.query(PureApiExternalPersonHst)
        .filter(and_(
          PureApiExternalPersonHst.uuid == person.uuid,
          PureApiExternalPersonHst.modified == person.modified,
        ))
        .one_or_none()
      )

      if person_hst is None:
        person_hst = PureApiExternalPersonHst(
          uuid=person.uuid,
          modified=person.modified,
          downloaded=person.downloaded
        )
        session.add(person_hst)

      pure_api_record_logger.info(person.json)
      session.delete(person)

def get_db_person(session, pure_uuid):
  return (
    session.query(Person)
    .filter(Person.pure_uuid == pure_uuid)
    .one_or_none()
  )

def create_db_person(api_person):
  return Person(
    uuid = str(uuid.uuid4()),
    pure_uuid = api_person.uuid,
    pure_internal = 'N',
  )

def run(
  # Do we need other default functions here?
  extract_api_persons=extract_api_persons,
  db_name=db_name,
  transaction_record_limit=transaction_record_limit,
  pure_api_record_logger=pure_api_record_logger,
  experts_etl_logger=experts_etl_logger
):
  with db.session(db_name) as session:
    processed_api_person_uuids = []
    for db_api_person in extract_api_persons(session):
      api_person = response.transform('external-persons', json.loads(db_api_person.json))      
      db_person = get_db_person(session, db_api_person.uuid)
      db_person_previously_existed = False
      if db_person:
        db_person_previously_existed = True
        if db_person.pure_modified and db_person.pure_modified >= db_api_person.modified:
          # Skip this record, since we already have a newer one:
          processed_api_person_uuids.append(db_api_person.uuid)
          continue
      else:   
        db_person = create_db_person(api_person)

      db_person.internet_id = None
      db_person.first_name = api_person.name.firstName
      db_person.last_name = api_person.name.lastName
      db_person.pure_modified = db_api_person.modified
    
      # Doubt that we will ever get these for external persons:
      db_person.orcid = None
      db_person.hindex = None
    
      # Check for orgs not in EDW yet:
    
      api_org_uuids = set()
      for org_assoc in api_person.externalOrganisations:
        api_org_uuids.add(org_assoc.uuid)
    
      db_org_uuids = set()
      if db_person_previously_existed:
        # Avoid trying to query a person that doesn't exist in the db yet:
        db_org_uuids = {db_org.pure_uuid for db_org in db_person.pure_orgs}
    
      api_only_org_uuids = api_org_uuids - db_org_uuids
      db_only_org_uuids = db_org_uuids - api_org_uuids
    
      # For now, skip this person if there are any orgs referenced in the api record
      # that we don't have in EDW:
      if len(api_only_org_uuids) > 0:
        api_only_orgs_in_db = session.query(PureOrg).filter(
          PureOrg.pure_uuid.in_(api_only_org_uuids)
        ).all()
        if len(api_only_org_uuids) > len(api_only_orgs_in_db):
          experts_etl_logger.info('Skipping updates for person with pure uuid {}: some associated orgs do not exist in EDW.'.format(api_person.uuid))
          continue

      # Now we can add the person to the session, because there are no other
      # reasons for intentionally skipping it:
      session.add(db_person)

      ## person pure orgs
    
      for org_uuid in api_only_org_uuids:
        person_pure_org = PersonPureOrg(
          person_uuid = db_person.uuid,
          pure_org_uuid = org_uuid,
        )
        session.add(person_pure_org)
    
      session.query(PersonPureOrg).filter(
        PersonPureOrg.person_uuid == db_person.uuid,
        PersonPureOrg.pure_org_uuid.in_(db_only_org_uuids)
      ).delete(synchronize_session=False)
    
      ## scopus ids
    
      db_scopus_ids = set()
      if db_person_previously_existed:
        # Avoid trying to query a person that doesn't exist in the db yet:
        db_scopus_ids = set(db_person.scopus_ids)
      person_ids = get_person_ids(api_person)
      api_only_scopus_ids = person_ids['scopus_ids'] - db_scopus_ids
      db_only_scopus_ids = db_scopus_ids - person_ids['scopus_ids']
    
      for scopus_id in api_only_scopus_ids:
        person_scopus_id = PersonScopusId(
          person_uuid = db_person.uuid,
          scopus_id = scopus_id,
        )
        session.add(person_scopus_id)
    
      session.query(PersonScopusId).filter(
        PersonScopusId.person_uuid == db_person.uuid,
        PersonScopusId.scopus_id.in_(db_only_scopus_ids)
      ).delete(synchronize_session=False)

      processed_api_person_uuids.append(api_person.uuid)
      if len(processed_api_person_uuids) >= transaction_record_limit:
        mark_api_persons_as_processed(session, pure_api_record_logger, processed_api_person_uuids)
        processed_api_person_uuids = []
        session.commit()

    mark_api_persons_as_processed(session, pure_api_record_logger, processed_api_person_uuids)
    session.commit()

  loggers.rollover(pure_api_record_logger)
