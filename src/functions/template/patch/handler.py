import json
import boto3
from datetime import datetime, timezone, timedelta
import os
import uuid
import copy

from dateutil import parser

def get_timestamp():
    fuso_horario = timezone(offset=timedelta(hours=-3))  # UTC-3
    data_e_hora_sao_paulo = datetime.now().astimezone(fuso_horario)
    return data_e_hora_sao_paulo.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def lambda_handler(event, context):
    requestID = "asasaas" #context.aws_request_id

    data_hora_atualizacao = get_timestamp()

    # dynamodb = boto3.resource("dynamodb", endpoint_url="http://localhost:8000")
    # table = dynamodb.Table("dev-mapper-dynamodb-table-templates")

    dynamo = boto3.resource("dynamodb")
    table = dynamo.Table(os.environ.get("dbtable_templates"))

    body = json.loads(event.get("body"))

    mapId=body.get("mapId")
    product=body.get("product")
    subproduct=body.get("subproduct")
    operation=body.get("operation")
    suboperation=body.get("suboperation")
    description=body.get("description")
    expectedInput=body.get("expectedInput")
    inputType=body.get("inputType")
    expectedOutput=body.get("expectedOutput")
    outputType=body.get("outputType")
    currentTemplate=body.get("currentTemplate")
    active=eval(str(body.get("active")).capitalize())

    if mapId == None:
        response = {
            "statusCode": 400,
            "body": json.dumps({
                "requestId": requestID,
                "errors": [
                    {
                        "status":400,
                        "code":"REQUISIÇÃO INVÁLIDA",
                        "title":"Requisição Inválida",
                        "detail":"O campo obrigatório mapId não foi encontrado no corpo da requisição."
                    }
                ]
            })
        }

        return response

    db_response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("mapId").eq(mapId)
    )

    if len(db_response.get("Items")) == 0:
        response = {
            "statusCode": 404,
            "body": json.dumps({
                "requestId": requestID,
                "errors": [
                    {
                        "status":404,
                        "code":"MAPEAMENTO NÃO ENCONTRADO",
                        "title":"Mapeamento não encontrado",
                        "detail":f"Não foi possível encontrar o mapeamento {mapId}."
                    }
                ]
            })
        }

        return response

    record = db_response.get("Items")[0]

    item = {}

    item["mapId"] = body.get("mapId")

    if body.get("product") != None:
        item["product"] = body.get("product")
    else:
        item["product"] = record.get("product")
    
    if body.get("subproduct") != None:
        item["subproduct"] = body.get("subproduct")
    else:
        item["subproduct"] = record.get("subproduct")

    if body.get("operation") != None:
        item["operation"] = body.get("operation")
    else:
        item["operation"] = record.get("operation")

    if body.get("suboperation") != None:
        item["suboperation"] = body.get("suboperation")
    else:
        item["suboperation"] = record.get("suboperation")

    if body.get("description") != None:
        item["description"] = body.get("description")
    else:
        item["description"] = record.get("description")

    if body.get("expectedInput") != None:
        item["expectedInput"] = body.get("expectedInput")
    else:
        item["expectedInput"] = record.get("expectedInput")

    if body.get("inputType") != None:
        item["inputType"] = body.get("inputType")
    else:
        item["inputType"] = record.get("inputType")

    if body.get("expectedOutput") != None:
        item["expectedOutput"] = body.get("expectedOutput")
    else:
        item["expectedOutput"] = record.get("expectedOutput")

    if body.get("outputType") != None:
        item["outputType"] = body.get("outputType")
    else:
        item["outputType"] = record.get("outputType")

    if body.get("currentTemplate") != None:
        item["currentTemplate"] = body.get("currentTemplate")
    else:
        item["currentTemplate"] = record.get("currentTemplate")

    if body.get("active") != None:
        item["active"] = eval(str(body.get("active")).capitalize())
    else:
        item["active"] = record.get("active")
    
    item["updateDate"] = data_hora_atualizacao

    tmp_list:list = copy.deepcopy(record.get("templateVersions"))
    tmp_record:dict = copy.deepcopy(record)
    tmp_record.pop("templateVersions", None)
    tmp_list.append(tmp_record)
    item["templateVersions"] = tmp_list

    db_response = insere_dyn_table_mapper(table, item)

    response = {
        "statusCode": 201,
        "body": json.dumps({
            "requestId": requestID,
            "data": item
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
            ":updateDate": item.get("updateDate"),
            ":active": item.get("active")
        },
        ReturnValues="UPDATED_NEW"
    )

    return response


event = {
    "body": json.dumps({
        "mapId": "4f4a3143-3122-4c87-ac86-b6b912d83877",
        "active": True
    })
}
resp = lambda_handler(event, None)
print(json.dumps(resp, indent=4))