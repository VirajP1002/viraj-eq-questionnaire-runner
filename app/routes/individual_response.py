from flask import Blueprint, g, redirect, request, url_for
from flask_login import current_user, login_required
from structlog import get_logger

from app.authentication.no_token_exception import NoTokenException
from app.globals import get_metadata, get_session_store
from app.helpers.language_helper import handle_language
from app.helpers.schema_helpers import with_schema
from app.helpers.session_helpers import with_questionnaire_store
from app.helpers.template_helper import render_template
from app.utilities.schema import load_schema_from_session_data
from app.views.handlers.individual_response import (
    IndividualResponseHandler,
    IndividualResponseHowHandler,
    IndividualResponsePostAddressConfirmHandler,
)

logger = get_logger()

individual_response_blueprint = Blueprint(
    name="individual_response", import_name=__name__, url_prefix="/individual-response/"
)


@individual_response_blueprint.before_request
def before_individual_response_request():
    metadata = get_metadata(current_user)
    if not metadata:
        raise NoTokenException(401)

    logger.bind(
        tx_id=metadata["tx_id"],
        schema_name=metadata["schema_name"],
        ce_id=metadata["collection_exercise_sid"],
        questionnaire_id=metadata["questionnaire_id"],
    )

    logger.info(
        "individual-response request", method=request.method, url_path=request.full_path
    )

    handle_language()

    session_store = get_session_store()
    g.schema = load_schema_from_session_data(session_store.session_data)


@individual_response_blueprint.route("/", methods=["GET", "POST"])
@login_required
@with_questionnaire_store
@with_schema
def request_individual_response(schema, questionnaire_store):
    language_code = get_session_store().session_data.language_code
    list_item_id = request.args.get("list_item_id")
    individual_response_handler = IndividualResponseHandler(
        block_definition=None,
        schema=schema,
        questionnaire_store=questionnaire_store,
        language=language_code,
        form_data=request.form,
        list_item_id=list_item_id,
    )

    if request.method == "GET":
        return individual_response_handler.handle_get()

    return redirect(url_for(".get_individual_response_how", list_item_id=list_item_id))


@individual_response_blueprint.route("/<list_item_id>/how", methods=["GET", "POST"])
@login_required
@with_questionnaire_store
@with_schema
def get_individual_response_how(schema, questionnaire_store, list_item_id):
    language_code = get_session_store().session_data.language_code
    individual_response_handler = IndividualResponseHowHandler(
        schema=schema,
        questionnaire_store=questionnaire_store,
        language=language_code,
        form_data=request.form,
        list_item_id=list_item_id,
    )

    if request.method == "GET" or not individual_response_handler.form.validate():
        return individual_response_handler.handle_get()

    return redirect(
        url_for(
            ".get_individual_response_post_address_confirm", list_item_id=list_item_id
        )
    )


@individual_response_blueprint.route(
    "/<list_item_id>/post/confirm-address", methods=["GET", "POST"]
)
@login_required
@with_questionnaire_store
@with_schema
def get_individual_response_post_address_confirm(
    schema, questionnaire_store, list_item_id
):
    language_code = get_session_store().session_data.language_code
    individual_response_handler = IndividualResponsePostAddressConfirmHandler(
        schema=schema,
        questionnaire_store=questionnaire_store,
        language=language_code,
        form_data=request.form,
        list_item_id=list_item_id,
    )

    if request.method == "GET" or not individual_response_handler.form.validate():
        return individual_response_handler.handle_get()

    return individual_response_handler.handle_post()


@individual_response_blueprint.route("/post/confirmation", methods=["GET", "POST"])
@login_required
@with_questionnaire_store
@with_schema
def get_individual_response_post_address_confirmation(schema, questionnaire_store):
    language_code = get_session_store().session_data.language_code
    IndividualResponseHandler(
        block_definition=None,
        schema=schema,
        questionnaire_store=questionnaire_store,
        language=language_code,
        form_data=request.form,
        list_item_id=None,
    )

    if request.method == "GET":
        return render_template(
            template="individual_response/confirmation",
            display_address=questionnaire_store.metadata.get("display_address"),
        )

    return redirect(url_for("questionnaire.get_questionnaire"))