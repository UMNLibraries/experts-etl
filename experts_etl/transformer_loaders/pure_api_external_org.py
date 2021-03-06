import json
from experts_dw import db
from sqlalchemy import and_, func
from experts_dw.models import PureApiExternalOrg, PureApiExternalOrgHst, PureOrg
from experts_etl import loggers
from pureapi import response
from pureapi.client import Config

# defaults:

db_name = 'hotel'
transaction_record_limit = 100
# Named for the Pure API endpoint:
pure_api_record_type = 'external-organisations'
pure_api_record_logger = loggers.pure_api_record_logger(type=pure_api_record_type)

def extract_api_orgs(session):
    for uuid in [result[0] for result in session.query(PureApiExternalOrg.uuid).distinct()]:
        orgs = session.query(PureApiExternalOrg).filter(
                PureApiExternalOrg.uuid == uuid
            ).order_by(
                PureApiExternalOrg.modified.desc()
            ).all()
        # The first record in the list should be the latest:
        yield orgs[0]

def mark_api_orgs_as_processed(session, pure_api_record_logger, processed_api_org_uuids):
    for uuid in processed_api_org_uuids:
        for org in session.query(PureApiExternalOrg).filter(PureApiExternalOrg.uuid==uuid).all():

            org_hst = (
                session.query(PureApiExternalOrgHst)
                .filter(and_(
                    PureApiExternalOrgHst.uuid == org.uuid,
                    PureApiExternalOrgHst.modified == org.modified,
                ))
                .one_or_none()
            )

            if org_hst is None:
                org_hst = PureApiExternalOrgHst(
                    uuid=org.uuid,
                    modified=org.modified,
                    downloaded=org.downloaded
                )
                session.add(org_hst)

            pure_api_record_logger.info(org.json)
            session.delete(org)

def get_db_org(session, pure_uuid):
    return (
        session.query(PureOrg)
        .filter(PureOrg.pure_uuid == pure_uuid)
        .one_or_none()
    )

def create_db_org(api_org):
    return PureOrg(
        pure_uuid = api_org.uuid,
        pure_internal = 'N',
        name_en = next(
            (name_text.value
                for name_text
                in api_org.name.text
                if name_text.locale =='en_US'
            ),
            None
        ),
    )

def run(
    # Do we need other default functions here?
    extract_api_orgs=extract_api_orgs,
    db_name=db_name,
    transaction_record_limit=transaction_record_limit,
    pure_api_record_logger=pure_api_record_logger,
    experts_etl_logger=None,
    pure_api_config=None
):
    if experts_etl_logger is None:
        experts_etl_logger = loggers.experts_etl_logger()
    experts_etl_logger.info('starting: transforming/loading', extra={'pure_api_record_type': pure_api_record_type})

    if pure_api_config is None:
        pure_api_config = Config()

    # Capture the current record for each iteration, so we can log it in case of an exception:
    api_org = None

    try:
        with db.session(db_name) as session:
            processed_api_org_uuids = []
            for db_api_org in extract_api_orgs(session):
                api_org = response.transform(
                    pure_api_record_type,
                    json.loads(db_api_org.json),
                    version=pure_api_config.version
                )
                db_org = get_db_org(session, db_api_org.uuid)
                if db_org:
                    if db_org.pure_modified and db_org.pure_modified >= db_api_org.modified:
                        # Skip this record, since we already have a newer one:
                        processed_api_org_uuids.append(db_api_org.uuid)
                        continue
                else:
                    db_org = create_db_org(api_org)

                db_org.name_en = next(
                    (name_text.value
                        for name_text
                        in api_org.name.text
                        if name_text.locale =='en_US'
                    ),
                    None
                )

                db_org.type = next(
                    (type_text.value
                        for type_text
                        in api_org.type.term.text
                        if type_text.locale =='en_US'
                    ),
                    None
                ).lower()

                db_org.pure_modified = db_api_org.modified
                session.add(db_org)

                processed_api_org_uuids.append(api_org.uuid)
                if len(processed_api_org_uuids) >= transaction_record_limit:
                    mark_api_orgs_as_processed(session, pure_api_record_logger, processed_api_org_uuids)
                    processed_api_org_uuids = []
                    session.commit()

            mark_api_orgs_as_processed(session, pure_api_record_logger, processed_api_org_uuids)
            session.commit()

    except Exception as e:
        formatted_exception = loggers.format_exception(e)
        experts_etl_logger.error(
            f'exception encountered during record transformation: {formatted_exception}',
            extra={'pure_uuid': api_org.uuid, 'pure_api_record_type': pure_api_record_type}
        )

    loggers.rollover(pure_api_record_logger)
    experts_etl_logger.info('ending: transforming/loading', extra={'pure_api_record_type': pure_api_record_type})
