import json
import boto3
import os
from urllib.parse import urlencode


def decorateDynamoDBResponse(response, queryStringParameters, requestID) -> dict:
    base_url = "/template?"

    prev = base_url + urlencode(queryStringParameters)

    if response.get("LastEvaluatedKey") != None:
        queryStringParameters["lastEvaluatedKey"] = response.get("LastEvaluatedKey").get("mapId")

    next = base_url + urlencode(queryStringParameters)

    queryStringParameters.pop("lastEvaluatedKey", None)
    first = base_url + urlencode(queryStringParameters)

    schema = {
        "meta": {
            "page": {
                "per-page": response.get("Count")
            }
        },
        "links": {
            "first": first,
            "prev": prev,
            "next": next
        },
        "requestId": requestID,
        "data": response.get("Items")
    }

    return schema


def lambda_handler(event, context):
    '''
    Habilita a pesquisa dos mappings por:
     - mapId
     - product |& operation
     - inputType |& outputType
     - active
    '''
    requestID = context.aws_request_id

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ.get("dbtable_templates"))

    # dynamodb = boto3.resource("dynamodb", endpoint_url="http://localhost:8000")
    # table = dynamodb.Table("dev-mapper-dynamodb-table-templates")
    # table_count = table.item_count

    queryStringParams = event.get("queryStringParameters")

    if queryStringParams == None:
        response = {
            "statusCode": 400,
            "body": json.dumps({
                "requestId":"a30ed1e4-de62-11eb-ba80-0242ac130004",
                "errors":[
                    {
                        "status":400,
                        "code":"BAD REQUEST",
                        "title":"Bad Request",
                        "detail":"Para realização da consulta, utilize ao menos um dos seguintes parâmetros: mapId, product, inputType"
                    }
                ]
            })
        }

        return response

    mapId = queryStringParams.get("mapId")
    product = queryStringParams.get("product")
    subproduct = queryStringParams.get("subproduct")
    operation = queryStringParams.get("operation")
    suboperation = queryStringParams.get("suboperation")
    inputType = queryStringParams.get("inputType")
    outputType = queryStringParams.get("outputType")
    active = queryStringParams.get("active")
    size = queryStringParams.get("size")
    lastEvaluatedKey = queryStringParams.get("lastEvaluatedKey")

    if active != None and active != "":
        try:
            active = eval(active.capitalize())
        except:
            active = None
    else:
        active = None

    if size != None and size != "":
        try:
            size = int(size)
        except:
            size = 100
    else:
        size = 100

    if lastEvaluatedKey != None and lastEvaluatedKey != "":
        try:
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key("mapId").eq(lastEvaluatedKey),
                # ProjectionExpression="mapId,product,operation,inputType,outputType"
            )
            if len(response["Items"]) > 0:
                lastEvaluatedKey = response["Items"][0]
            else:
                lastEvaluatedKey = None
        except:
            lastEvaluatedKey = None
    else:
        lastEvaluatedKey = None

    response = None

    if mapId != None:
        # Se mapId está presente, faz a consulta apenas pelo mapId e retorna 1 ou nenhum
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("mapId").eq(mapId),
            # ProjectionExpression="mapId,product,subproduct,operation,suboperation,inputType,outputType,active"
        )
        
        response = decorateDynamoDBResponse(response, queryStringParams, requestID)
    else:
        if product != None:
            # Se product está presente, faz a consulta usando o índice product-operation-index
            index_expr = "product = :product "
            expr_attr_values = {
                ":product": product
            }
            
            if operation != None and operation != "":
                index_expr = index_expr + " AND operation = :operation "
                expr_attr_values[":operation"] = operation
            
            expr_filter = ""
            if active != None and active != "":
                expr_attr_values[":active"] = active
                expr_filter = "active = :active "
            else:
                expr_attr_values[":active"] = None
                expr_filter = "active <> :active "
            
            if subproduct != None and subproduct != "":
                expr_attr_values[":subproduct"] = subproduct
                expr_filter = expr_filter + " AND subproduct = :subproduct "

            if suboperation != None and suboperation != "":
                expr_attr_values[":suboperation"] = suboperation
                expr_filter = expr_filter + " AND suboperation = :suboperation "

            if inputType != None and inputType != "":
                expr_attr_values[":inputType"] = inputType
                expr_filter = expr_filter + " AND inputType = :inputType "

            if outputType != None and outputType != "":
                expr_attr_values[":outputType"] = subproduct
                expr_filter = expr_filter + " AND outputType = :outputType "

            if lastEvaluatedKey != None:
                response = table.query(
                    IndexName="product-operation-index",
                    KeyConditionExpression=index_expr,
                    # ProjectionExpression="mapId,product,subproduct,operation,suboperation,inputType,outputType,active",
                    ExpressionAttributeValues=expr_attr_values,
                    FilterExpression=expr_filter,
                    Limit=size,
                    ExclusiveStartKey={
                        "mapId": lastEvaluatedKey.get("mapId"),
                        "product": lastEvaluatedKey.get("product"),
                        "operation": lastEvaluatedKey.get("operation")
                    }
                )

                response = decorateDynamoDBResponse(response, queryStringParams, requestID)
            else:
                response = table.query(
                    IndexName="product-operation-index",
                    KeyConditionExpression=index_expr,
                    # ProjectionExpression="mapId,product,subproduct,operation,suboperation,inputType,outputType,active",
                    ExpressionAttributeValues=expr_attr_values,
                    FilterExpression=expr_filter,
                    Limit=size
                )

                response = decorateDynamoDBResponse(response, queryStringParams, requestID)
        elif inputType != None:
            # Se inputType está presente, faz a consulta usando o índice inputType-outputType-index
            index_expr = "inputType = :inputType "
            expr_attr_values = {
                ":inputType": inputType
            }
            
            if outputType != None and outputType != "":
                index_expr = index_expr + " AND outputType = :outputType "
                expr_attr_values[":outputType"] = outputType
            
            expr_filter = ""
            if active != None and active != "":
                expr_attr_values[":active"] = active
                expr_filter = "active = :active "
            else:
                expr_attr_values[":active"] = None
                expr_filter = "active <> :active "
            
            if subproduct != None and subproduct != "":
                expr_attr_values[":subproduct"] = subproduct
                expr_filter = expr_filter + " AND subproduct = :subproduct "

            if suboperation != None and suboperation != "":
                expr_attr_values[":suboperation"] = suboperation
                expr_filter = expr_filter + " AND suboperation = :suboperation "

            if product != None and product != "":
                expr_attr_values[":product"] = product
                expr_filter = expr_filter + " AND product = :product "

            if operation != None and operation != "":
                expr_attr_values[":operation"] = operation
                expr_filter = expr_filter + " AND operation = :operation "

            if lastEvaluatedKey != None:
                response = table.query(
                    IndexName="inputType-outputType-index",
                    KeyConditionExpression=index_expr,
                    # ProjectionExpression="mapId,product,subproduct,operation,suboperation,inputType,outputType,active",
                    ExpressionAttributeValues=expr_attr_values,
                    FilterExpression=expr_filter,
                    Limit=size,
                    ExclusiveStartKey={
                        "mapId": lastEvaluatedKey.get("mapId"),
                        "inputType": lastEvaluatedKey.get("inputType"),
                        "outputType": lastEvaluatedKey.get("outputType")
                    }
                )

                response = decorateDynamoDBResponse(response, queryStringParams, requestID)
            else:
                response = table.query(
                    IndexName="inputType-outputType-index",
                    KeyConditionExpression=index_expr,
                    # ProjectionExpression="mapId,product,subproduct,operation,suboperation,inputType,outputType,active",
                    ExpressionAttributeValues=expr_attr_values,
                    FilterExpression=expr_filter,
                    Limit=size
                )

                response = decorateDynamoDBResponse(response, queryStringParams, requestID)
        else:
            response = {
                "statusCode": 400,
                "body": json.dumps({
                    "requestId":"a30ed1e4-de62-11eb-ba80-0242ac130004",
                    "errors":[
                        {
                            "status":400,
                            "code":"BAD REQUEST",
                            "title":"Bad Request",
                            "detail":"Para realização da consulta, utilize ao menos um dos seguintes parâmetros: mapId, product, inputType"
                        }
                    ]
                })
            }

            return response

    response = {
        "statusCode": 200,
        "body": json.dumps(response)
    }

    return response


#### TESTE ####
# event = {
#     "queryStringParameters" : {
#         "product": "pix",
#         "size": 5,
#         "lastEvaluatedKey": "ac586753-0b96-4514-8936-3a5b3c567f41"
#     }
# }
# response = lambda_handler(event, None)

# print(json.dumps(json.loads(response.get("body")), indent=4))