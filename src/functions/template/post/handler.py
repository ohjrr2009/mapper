import json
import boto3
from datetime import datetime, timezone, timedelta
import os
import uuid

from dateutil import parser

def get_timestamp():
    fuso_horario = timezone(offset=timedelta(hours=-3))  # UTC-3
    data_e_hora_sao_paulo = datetime.now().astimezone(fuso_horario)
    return data_e_hora_sao_paulo.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def lambda_handler(event, context):
    requestID = context.aws_request_id

    # dynamodb = boto3.resource("dynamodb", endpoint_url="http://localhost:8000")
    # table = dynamodb.Table("dev-mapper-dynamodb-table-templates")

    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table(os.environ.get("dbtable_templates"))

    body = json.loads(event.get("body"))

    item = {
        "mapId": str(uuid.uuid4()),
        "product": body.get("product"),
        "subproduct": body.get("subproduct"),
        "operation": body.get("operation"),
        "suboperation": body.get("suboperation"),
        "description": body.get("description"),
        "expectedInput": body.get("expectedInput"),
        "inputType": body.get("inputType"),
        "expectedOutput": body.get("expectedOutput"),
        "outputType": body.get("outputType"),
        "currentTemplate": body.get("currentTemplate"),
        "templateVersions": [],
        "insertionDate": get_timestamp(),
        "updateDate": None,
        "active": True
    }

    try:
        db_response = insere_dyn_table_mapper(table, item)

        print(db_response)

        response = {
            "statusCode": 201,
            "body": json.dumps({
                "requestId": requestID,
                "data": {
                    "mapId": item.get("mapId")
                }
            })
        }

        return response
    except Exception as error:
        print(error)

        response = {
            "statusCode": 500,
            "body": json.dumps({
                "requestId": requestID,
                "errors":[
                    {
                        "status":500,
                        "code":"INTERNAL SERVER ERROR",
                        "title":"Erro Interno de Servidor",
                        "detail":"Não foi possivel realizar a inserção do item. Favor verificar o log e/ou contate o administrador do sistema."
                    }
                ]
            })
        }

        return response


def insere_dyn_table_mapper(table, item: dict):
    update_string = "set product = :product, " \
                    "subproduct = :subproduct, " \
                    "operation = :operation, " \
                    "suboperation = :suboperation, " \
                    "description = :description, " \
                    "expectedInput = :expectedInput, " \
                    "inputType = :inputType, " \
                    "expectedOutput = :expectedOutput, " \
                    "outputType = :outputType, " \
                    "currentTemplate = :currentTemplate, " \
                    "templateVersions = :templateVersions, " \
                    "insertionDate = :insertionDate, " \
                    "updateDate = :updateDate, " \
                    "active = :active"

    response = table.update_item(
        Key={
            "mapId": str(item.get("mapId"))
        },
        UpdateExpression=update_string,
        ExpressionAttributeValues={
            ":product": str(item.get("product")),
            ":subproduct": str(item.get("subproduct")),
            ":operation": str(item.get("operation")),
            ":suboperation": str(item.get("suboperation")),
            ":description": str(item.get("description")),
            ":expectedInput": str(item.get("expectedInput")),
            ":inputType": str(item.get("inputType")),
            ":expectedOutput": str(item.get("expectedOutput")),
            ":outputType": str(item.get("outputType")),
            ":currentTemplate": str(item.get("currentTemplate")),
            ":templateVersions": item.get("templateVersions"),
            ":insertionDate": str(item.get("insertionDate")),
            ":updateDate": item.get("updateDate"),
            ":active": item.get("active")
        },
        ReturnValues="UPDATED_NEW"
    )

    return response


event = {
    "body": json.dumps({})
}
resp = lambda_handler(event, None)
print(resp)