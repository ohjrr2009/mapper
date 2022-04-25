import json

from botocore import config
from mapper import InputOrigin, Mapper, MapperType
import boto3
import os
import sys

# {
#     "config": {
#         "mapId": "uuid",
#         "inputOrigin": "AWS_EVENT"
#     },
#     "payload": "evento como string"
# }

def lambda_handler(event, context):
    try:
        requestID = context.aws_request_id

        dynamo = boto3.resource("dynamodb")
        table_templates = dynamo.Table(os.environ.get("dbtable_templates"))
        
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)

        config = body.get("config")
        payload = body.get("payload")
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        mapId = config.get("mapId")
        inputOrigin = None
        
        if config.get("inputOrigin") != None and config.get("inputOrigin") == "AWS_EVENT":
            inputOrigin = InputOrigin.AWS_EVENT
        else:
            inputOrigin = InputOrigin.DEFAULT

        result = retorna_map_info(table_templates, mapId)

        if result == None:
            response = {
                "statusCode": 404,
                "body": json.dumps({
                    "requestId": requestID,
                    "errors":[
                        {
                            "status":404,
                            "code":"TEMPLATE DE MAPEAMENTO NÃO ENCONTRADO",
                            "title":"Template de mapeamento não encontrado",
                            "detail":"O mapId informado não possui nenhum template associado."
                        }
                    ]
                })
            }
        
            return response

        if not result.get("active"):
            response = {
                "statusCode": 403,
                "body": json.dumps({
                    "requestId": requestID,
                    "errors":[
                        {
                            "status":403,
                            "code":"TEMPLATE NÃO ESTÁ ATIVO E NÃO PODE SER USADO",
                            "title":"Template de mapeamento não está ativo",
                            "detail":"O mapId informado corresponde a um template desativado."
                        }
                    ]
                })
            }
        
            return response
    
        mapperType = None
        if result.get("inputType") == "JSON" and result.get("outputType") == "JSON":
            mapperType = MapperType.JSON_TO_JSON
        elif result.get("inputType") == "JSON" and result.get("outputType") == "XML":
            mapperType = MapperType.JSON_TO_XML
        elif result.get("inputType") == "XML" and result.get("outputType") == "JSON":
            mapperType = MapperType.XML_TO_JSON    
        elif result.get("inputType") == "XML" and result.get("outputType") == "XML":
            mapperType = MapperType.XML_TO_XML
        
        mapper = Mapper(
            type=mapperType,
            template=result.get("currentTemplate"),
            input=payload,
            input_origin=inputOrigin)
        
        body = None
        if result.get("outputType") == "XML":
            body = mapper.map()
        else:
            body = json.dumps({
                "requestId": requestID,
                "data": mapper.map()
            })

        response = {
            "statusCode": 201,
            "body": body,
            "headers":{
                "Content-Type": "text/xml" if result.get("outputType") == "XML" else "application/json"
            }
        }
    
        return response
    except Exception as error:
        print("Exception >>> ",error)
        response = {
            "statusCode": 400,
            "body": json.dumps({
                "requestId": requestID,
                "errors":[
                    {
                        "status":400,
                        "code":"BAD REQUEST",
                        "title":"Bad Request",
                        "detail":"Não foi possivel realizar o processo de conversão com o mapId " + mapId + " e o input fornecido. Favor verificar o log e/ou contate o administrador do sistema."
                    }
                ]
            })
        }
    
        return response


def retorna_map_info(table, mapId):
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("mapId").eq(mapId)
    )
    if response.get("Items") == None or len(response["Items"]) == 0:
        return None
    return response["Items"][0]