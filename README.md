# Description

Project that defines the REST API to be used as a payload mapping and/or conversion tool, between the following formats:
* **JSON -> JSON**
* **JSON -> XML**
* **XML -> JSON**
* **XML -> XML**

Each mapping uses Templates written in [**Velocity Template Language (VTL)**](https://velocity.apache.org/engine/1.7/user-guide.html), in this way most of the known VTL functions can be used for elaborating Templates.

The Project, however, still allows the addition of Generic Custom Functions and Custom Functions at the domain level, simply by adding such functions in the Python script called [mapper.py](layer/python/lib/python3.8/site-packages/mapper.py) (script that is part of the Layer **mapper-api-lambda-layer**) 

The Project was written using the language **Python 3.8** and use [**AirSpeed**](https://github.com/purcell/airspeed) as **VTL Engine**.

Macros in VTL are also allowed and follow the writing standards established by the language. Such macros can be added to the mapping process embedded in the Template or even as a list of macros to be passed to the mapping function.

## Preparing the Development and Test Environment
### Installation
You must have the following technologies installed on your machine to be able to work on the project:
* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
* [npm](https://www.npmjs.com/get-npm)
* [Serverless Framework](https://www.serverless.com/framework/docs/getting-started/)
* [VS Code](https://code.visualstudio.com/Download) or another IDE

### Configurações
To test the project in the development environment, you must have the AWS CLI configured on your machine, which is the client to publish the project as a stack via AWS Cloudformation. To do this, you need, with the AWS CLI already installed, open a command prompt and type the following command, answering the questions then as shown in the example below, as instructed in [official docs](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html):

```bash
$ aws configure
AWS Access Key ID [None]: ********************
AWS Secret Access Key [None]: ****************************
Default region name [None]: us-east-2
Default output format [None]: json
```

## Deployment Procedures
This project is composed of source code written in Python and exposes 4 endpoints in an Api Gateway.

To deploy the project in **dev**, just run the following command from the command prompt inside the project's root directory.

```bash
$ sls deploy
```

If you want to remove the created stack, use the command:

```bash
$ sls remove
```

## MAPPER - Specifying REST API Endpoints

**MAPPER - REST API endpoints in DEV Environment**

* **POST_MAP**
  * **POST** - https://<env>/dev/core/mapper/map
   * **Description:** Endpoint dedicated to mapping a particular payload according to the rules established by the Template
   * **Parameters:**
     *  *body*:string (Body - mandatory) - The body is composed of 2 mandatory properties which are **config** and **payload**. The first is responsible for passing information related to the Template (*mapId*) and the origin type of the mapping process (*inputOrigin*). The second is responsible for storing the payload that will actually be converted/mapped according to the rules established in the Template. There are 2 types of **inputOrigin**: **AWS_EVENT** and **DEFAULT**. The **DEFAULT** type is the default and is used for any type of payload, whether JSON or XML, the root of the document in question will be referenced within the Template in VTL by the **inputRoot** property. In the case of the **AWS_EVENT** type, this is used when an event received by an AWS Lambda must be read and mapped, in this situation, more properties will be available within the VTL Template, namely: **inputRoot**, ** inputHeaders**, **inputQueryStringParameters**, **inputpathParameters** and **inputBody**.

        ```JSON
        {
            "config": {
                "mapId": map_id,
                "inputOrigin": "AWS_EVENT"
            },
            "payload": event
        }
        ```
    * **Responses:**
      - **201**: Indicates that the mapping process was successful. In the header the field **Content-Type** will be defined as **text/xml** if the **outputType** of the Template is XML or **application/json**, otherwise.
        - Response body for case **outputType** as a JSON:
          ```JSON
          {
            "requestId": string,
            "data": string
          }
          ```
        - Response body for case **outputType** as a XML:
          ```XML
          <?xml version="1.0" encoding="UTF-8"?>
          <nome_da_tag_raiz>
            ...
          </nome_da_tag_raiz>
          ```
      - **400**: Bad Request, indicating that it was not possible to carry out the mapping process with the mapId and the input provided.
        ```JSON
        {
          "status":400,
          "code":"BAD REQUEST",
          "title":"Bad Request",
          "detail":"It was not possible to perform the conversion process with the mapId and the input provided. Please check the log and/or contact your system administrator."
        }
        ```
      - **403**: Forbidden, indicating that it was not possible to perform the conversion process with the mapId provided because it is disabled.
        ```JSON
        {
            "requestId": requestID,
            "errors":[
                {
                    "status":403,
                    "code":"TEMPLATE IS NOT ACTIVE AND CANNOT BE USED",
                    "title":"Mapping template is not active",
                    "detail":"The mapId informed corresponds to a deactivated template."
                }
            ]
        }
        ```
      - **404**: The mapId informed does not have any associated template.
        ```JSON
        {
          "status":404,
          "code":"MAPPING TEMPLATE NOT FOUND",
          "title":"Mapping template not found",
          "detail":"The mapId informed does not have any associated template."
        }
        ``` 
  

* **POST_MAPPER_TEMPLATE**
  * **POST** - https://<env>/dev/core/mapper/template
   * **Description:** Insert a new template into the table **\<env>-mapper-dynamodb-table-templates**
   * **Parameters:**
     *  *body*:string (Body - mandatory) - The body is composed with the properties below:
        ```JSON
        {
          "product": string,
          "subproduct": string,
          "operation": string,
          "suboperation": string,
          "description": string,
          "expectedInput": string,
          "inputType": string,
          "expectedOutput": string,
          "outputType": string,
          "currentTemplate": string
        }
        ```
        Additionally during the insertion process, the properties **mapId** (it's a **UUID v4**), *templateVersions*, *insertionDate*, *updateDate* and *active* (*true* by default) will be added to the item in the table. It should be noted that the mapId will be automatically generated by the endpoint.

    * **Responses:**
      - **201**: Indicates that the template insertion process was successful.
          ```JSON
          {
            "requestId": string,
            "data": {
                "mapId": string
            }
          }
          ```
      - **500**: Internal server error, indicating that it was not possible to perform the template insertion process with the parameters provided.
        ```JSON
        {
          "requestId": string,
          "errors":[
            {
              "status":500,
              "code":"INTERNAL SERVER ERROR",
              "title":"Internal Server Error",
              "detail":"Unable to insert the item. Please check the log and/or contact your system administrator."
            }
          ]
        }
        ```

* **GET_MAPPER_TEMPLATE**
  * **GET** - https://<env>/dev/core/mapper/template
   * **Description:** Returns a list of Templates. To perform the query, at least one of the following parameters must be used: **mapId**, **product**, **inputType**. The **lastEvaluatedKey** parameter must always be passed to ensure the paging process. The **lastEvaluatedKey** parameter is always present in the page response as a result of the query.
   * **Parameters:**
     *  *mapId*:string (Query - Optional) - is the UUID that represents the template. This field must be used whenever you want to restrict the query by looking for only the template with the informed mapId.
     *  *product*:string (Query - Optional) - is the category of related templates by product.
     *  *subproduct*:string (Query - Optional) - is the category of templates related by subproduct.
     *  *operation*:string (Query - Optional) - is the category of templates related by operation.
     *  *suboperation*:string (Query - Optional) - is the category of templates related by operation.
     *  *inputType*:string (Query - Optional) - indicates the type of payload input [XML or JSON].
     *  *outputType*:string (Query - Optional) - indicates the type of payload output [XML or JSON].
     *  *active*:string (Query - Optional) - indicates whether the template is active or not for mapping.
     *  *size*:string (Query - Optional) - page size to be returned. Default: 100.
     *  *lastEvaluatedKey*:string (Query - Optional) - indicates the value of the last key returned on the page. This parameter is used to continue the paging process together with DynamoDB, if not used, the query will always return the first page.

   * **Responses:**
      - **200**: Indicates that the template insertion process was successful.
          ```JSON
          {
            "meta": {
              "page": {
                "per-page": number
              }
            },
            "links": {
              "first": string,
              "prev": string,
              "next": string
            },
            "requestId": string,
            "data": [
              ... object ...
            ]
          }
          ```
      - **400**: Internal server error, indicating that it was not possible to perform the template insertion process with the parameters provided.
        ```JSON
        {
          "requestId":"a30ed1e4-de62-11eb-ba80-0242ac130004",
          "errors":[
            {
              "status":400,
              "code":"BAD REQUEST",
              "title":"Bad Request",
              "detail":"To perform the query, use at least one of the following parameters: mapId, product, inputType"
            }
          ]
        }
        ```

* **PATCH_MAPPER_TEMPLATE**
  * **PATCH** - https://<env>/dev/core/mapper/template
   * **Description:** Update a table template **\<env>-mapper-dynamodb-table-templates**
   * **Parameters:**
     *  *body*:string (Body - mandatory) - The body is composed of the properties below:
        ```JSON
        {
          "mapId": string (mandatory field),
          "product": string,
          "subproduct": string,
          "operation": string,
          "suboperation": string,
          "description": string,
          "expectedInput": string,
          "inputType": string,
          "expectedOutput": string,
          "outputType": string,
          "currentTemplate": string,
          "active": bool
        }
        ```

    * **Responses:**
      - **201**: Indicates that the template insertion process was successful.
          ```JSON
          {
            "requestId": string,
            "data": {
                ...inserted item...
            }
          }
          ```
      - **400**: Bad Request, indicating that it was not possible to perform the Template update process with the parameters provided.
        ```JSON
        {
          "requestId": string,
          "errors": [
            {
              "status":400,
              "code":"INVALID REQUEST",
              "title":"Invalid Request",
              "detail":"Mandatory field mapId not found in request body."
            }
          ]
        }
        ```
      - **404**: NOT FOUND, indicating that it was not possible to perform the Template update process with the parameters provided.
        ```JSON
        {
          "requestId": string,
          "errors": [
            {
              "status":404,
              "code":"MAPPING NOT FOUND",
              "title":"Mapping not found",
              "detail":"Could not find mapping with the given mapId."
            }
          ]
        }
        ```

## Utilização
Below are examples of the 4 types of mapping allowed for Mapper:

* **JSON -> JSON**
  * **INPUT**
    ```JSON
    {
      "name":"John",
      "surname":"Silva",
      "age":20,
      "birthdate":"1984-02-04",
      "address":{
          "street":"Albert's Street",
          "City":"Test City",
          "complementos":{
            "apt":"1111"
          }
      },
      "role":[
          "admin",
          "user"
      ],
      "prices":[
          12.40,
          11.11
      ],
      "ativo":false,
      "ativo2":null
    }
    ```

  * **EXAMPLE OF TEMPLATE**
    ```JSON
    {
      "name": {
        "firstname": #validate($inputRoot.name, "string"),
        "lastname": #validate($inputRoot.surname, "string"),
        "price": #validate($inputRoot.price, "number"),
        "ativo": #validate($inputRoot.ativo, "boolean"),
        "ativo2": #validate($inputRoot.ativo2, "string")
      },
      #if ($!inputRoot.birthplace)
        "birthplace": "FIELD DOES NOT EXIST AND WILL NOT BE SHOWN",
      #end
      "mobile": #validate($inputRoot.mobile, "string"),
      "role":  #validate($inputRoot.role, "object"),
      "address": {
        "country": #validate($inputRoot.address.country, "string"),
        "state": #validate($inputRoot.address.state, "string"),
        "city": #validate($inputRoot.address.City, "string"),
        "street": #validate($inputRoot.address.street, "string")
      },
      "email": #validate($inputRoot.email, "string"),
      "prices": [
        #foreach($item in $inputRoot.prices)
          #validate($item, "string"),
        #end
      ],
      "address1": $inputRoot.address
    }
    ```

  * **OUTPUT**
    ```JSON
    {
      "name": {
        "firstname": "John",
        "lastname": "Silva",
        "price": null,
        "ativo": false,
        "ativo2": null
      },
      "mobile": null,
      "role": [
        "admin",
        "user"
      ],
      "address": {
        "country": null,
        "state": null,
        "city": "Test City",
        "street": "Albert's Street"
      },
      "email": null,
      "prices": [
        "12.4",
        "11.11"
      ],
      "address1": {
        "street": "Albert's Street",
        "City": "Test City",
        "complementos": {
            "apt": "1111"
        }
      }
    }
    ```

* **JSON -> XML**
  * **INPUT**
    ```JSON
    {
      "audience":{
        "id":{
          "what":"attribute",
          "text":"123"
        },
        "name":"Shubham"
      }
    }
    ```
  * **EXAMPLE OF TEMPLATE**
    ```XML
    <audience>
      <id what=#validate($inputRoot.audience.id.what, "string")>#validate($inputRoot.audience.id.text, "object")</id>
      <name>#validate($inputRoot.audience.name, "object")</name>
    </audience>
    ```
  * **OUTPUT**
    ```XML
    <?xml version="1.0" encoding="UTF-8"?>
    <audience>
      <id what="attribute">123</id>
      <name>Shubham</name>
    </audience>
    ```

* **XML -> JSON**
  * **INPUT**
    ```XML
    <?xml version="1.0" encoding="UTF-8"?>
    <student>
      <id>FA18-RSE-012</id>
      <name what="teste">
        <firstName>Kamran</firstName>
        <middleName>Kamran</middleName>
        <lastName>Kamran</lastName>
      </name>
      <email>kamran@example.com</email>
      <smeseter>4</smeseter>
      <class>MSSE</class>
      <subjects>
        <sub1>ASPMI</sub1>
        <sub2>ASQA</sub2>
        <sub3>ASPM</sub3>
        <sub4>Semantic Web</sub4>
      </subjects>
    </student>
    ```
  * **EXAMPLE OF TEMPLATE**
    ```JSON
    {
      "student": {
        "id": #validate($inputRoot.student.id, "string"),
        "name": {
          "what": #validate($inputRoot.student.name["@what"], "string"),
          "firstName": #validate($inputRoot.student.name.firstName, "string"),
          "middleName": #validate($inputRoot.student.name.middleName, "string"),
          "lastName": #validate($inputRoot.student.name.lastName, "string")
        },
        "email": #validate($inputRoot.student.email, "string"),
        "semester": #validate($inputRoot.student.smeseter, "number"),
        "class": #validate($inputRoot.student.class, "string"),
        "subjects": {
          "sub1": #validate($inputRoot.student.subjects.sub1, "string"),
          "sub2": #validate($inputRoot.student.subjects.sub2, "string"),
          "sub3": #validate($inputRoot.student.subjects.sub3, "string"),
          "sub4": #validate($inputRoot.student.subjects.sub4, "string")
        }
      }
    }
    ```
  * **OUTPUT**
    ```JSON
    {
      "student": {
        "id": "FA18-RSE-012",
        "name": {
          "what": "teste",
          "firstName": "Kamran",
          "middleName": "Kamran",
          "lastName": "Kamran"
        },
        "email": "kamran@example.com",
        "semester": 4,
        "class": "MSSE",
        "subjects": {
          "sub1": "ASPMI",
          "sub2": "ASQA",
          "sub3": "ASPM",
          "sub4": "Semantic Web"
        }
      }
    }
    ```

* **XML -> XML**
  * **INPUT**
    ```XML
    <?xml version="1.0" encoding="UTF-8"?>
    <student>
      <id>FA18-RSE-012</id>
      <name what="teste">
        <firstName>Kamran</firstName>
        <middleName>Kamran</middleName>
        <lastName>Kamran</lastName>
      </name>
      <email>kamran@example.com</email>
      <smeseter>4</smeseter>
      <class attr="atributo">MSSE</class>
      <subjects>
        <sub1>ASPMI</sub1>
        <sub2>ASQA</sub2>
        <sub3>ASPM</sub3>
        <sub4>Semantic Web</sub4>
      </subjects>
    </student>
    ```
  * **EXAMPLE OF TEMPLATE**
    ```XML
    <estudante>
      <id>#validate($inputRoot.student.id, "object")</id>
      <nome what=#validate($inputRoot.student.name["@what"], "string")>
        <primeiroNome>#validate($inputRoot.student.name.firstName, "object")</primeiroNome>
        <nomeDoMeio>#validate($inputRoot.student.name.middleName, "object")</nomeDoMeio>
        <ultimoNome>#validate($inputRoot.student.name.lastName, "object")</ultimoNome>
      </nome>
      <semestre>#validate($inputRoot.student.smeseter, "object")</semestre>
      <email>#validate($inputRoot.student.email, "object")</email>
      <classe>#validate($inputRoot.student.class["#text"], "object")</classe>
      <disciplinas>
        #foreach($key in $inputRoot.student.subjects)
          #if ($key == "sub1" || $key == "sub2")
            <$key>#validate($inputRoot.student.subjects.get($key), "object")</$key>
          #end
        #end
      </disciplinas>
    </estudante>
    ```
  * **OUTPUT**
    ```XML
    <?xml version="1.0" encoding="UTF-8"?>
    <estudante>
      <id>FA18-RSE-012</id>
      <nome what="teste">
        <primeiroNome>Kamran</primeiroNome>
        <nomeDoMeio>Kamran</nomeDoMeio>
        <ultimoNome>Kamran</ultimoNome>
      </nome>
      <semestre>4</semestre>
      <email>kamran@example.com</email>
      <classe>MSSE</classe>
      <disciplinas>
        <sub1>ASPMI</sub1>
        <sub2>ASQA</sub2>
      </disciplinas>
    </estudante>
    ```
* **Observações:**
  * The **#validate(\$field, \<type>)** macro function is a macro created to be used optionally, even though it is available in the Mapper tool. The main purpose of the function is to prevent returns badly processed by the VTL engine from existing in the output (eg. string with VTL code or blank). It is therefore recommended that the macro is always used. The function receives as input 02 (two) parameters: $field (which is the input field where the input data will be read to be validated) and \<type> which can be any of the types:
    * **"string"**: guarantees that the validated data will be returned as a string
    * **"number"**: guarantees that the validated data will be returned as a number
    * **"boolean"**: guarantees that the validated data will be returned as a boolean
    * **"object"**: guarantees that the validated data will be returned unchanged from the original

## CUSTOM FUNCTIONS
  * In addition to the basic functions of the VTL engine, the Mapper tool also provides the following general-purpose functions:
    * **"string".substring(start, end)**: returns a substring of a given string passing the start and end indices as parameters. Ex.
      ```
      "countryCode": #validate($inputBody.txChave.substring(1, 3), "number")
      ```
    * **"string".contains(text)**: returns a boolean indicating whether or not a given string is contained in another.
    * **"string".convert_timezone(from_tz, to_tz)**: convert a datetime from one timezone, represented by a string, to another date_time from another time_zone and return the new representation in the pattern **("%Y-%m-%dT%H:%M:%S.%fZ")**. Ex.
      ```
      "referenceDate": #validate($inputHeaders.timestamp.convert_timezone(0,0), "string")
      ```
    * **"string".get_date(str_time)**: extracts only the date from a date_time represented by a string, the pattern of the end date must be passed as a parameter to the function. Ex.  
      ```
      "openingDate": #validate($inputBody.pix.dtPagto.get_date("%Y-%m-%dT00:00:00.000+00:00"), "string")
      ```