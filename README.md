# Descrição

Projeto que define a API REST para ser utilizada como ferramenta de mapeamento e/ou conversão de payloads, quais sejam:
* **JSON -> JSON**
* **JSON -> XML**
* **XML -> JSON**
* **XML -> XML**

Cada conversão se utiliza de Templates escritos em [**Velocity Template Language (VTL)**](https://velocity.apache.org/engine/1.7/user-guide.html), dessa maneira grande parte das funções VTL conhecidas podem ser utilizadas.

O Projeto, no entanto, ainda permite a adição de Funções Genéricas Customizadas e Funções Customizadas ao nível de domínio, bastando para tanto, adicionar tais funções no script em Python denominado [mapper.py](layer/python/lib/python3.8/site-packages/mapper.py) (script esse que faz parte da Layer **mapper-api-lambda-layer**) 

O Projeto foi escrito com uso da linguagem **Python 3.8** e usa como **motor VTL** o [**AirSpeed**](https://github.com/purcell/airspeed).

Macros em VTL também são permitidas e seguem os padrões de escrita estabelecidos pela linguagem. Tais macros podem ser adicionadas ao processo de mapeamento embutidas junto ao Template ou mesmo como uma lista de macros a ser passada para a função de mapeamento.

## Preparando o Ambiente de Desenvolvimento e Testes
### Instalações
É preciso ter instalado em sua máquina as seguintes tecnologias para poder atuar no projeto:
* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
* [npm](https://www.npmjs.com/get-npm)
* [Serverless Framework](https://www.serverless.com/framework/docs/getting-started/)
* [VS Code](https://code.visualstudio.com/Download) como IDE sugerida

### Configurações
Para testar o projeto em ambiente de desenvolvimento é necessário possuir configurado em sua máquina o AWS CLI, que é o client para publicar o projeto como uma stack via AWS Cloudformation. Para isso, é preciso, com o AWS CLI instalado, abra um promt de comando e digite o comando a seguir, respondendo as perguntas em seguida conforme o exemplo abaixo, conforme orientado na [documentação oficial](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html):

```bash
$ aws configure
AWS Access Key ID [None]: ********************
AWS Secret Access Key [None]: ****************************
Default region name [None]: us-east-2
Default output format [None]: json
```

Entre em contato com o time de infraestrutura para obter o **AWS Access Key ID** e o **AWS Secret Access Key** para o ambiente de desenvolvimento.

## Procedimentos de Deploy
Este projeto é composto pelo código fonte escrito em Python e expõe 4 endpoints na Api Gateway denominada **\<env>-internal-api**.

Para a realização do deploy  do projeto em **dev** basta que no prompt de comando executemos o seguinte comando dentro do diretório raiz do projeto.

```bash
$ sls deploy --env dev
```

Caso você queira remover a stack criada, utilize o comando:

```bash
$ sls remove --env dev
```

## MAPPER - Especificação dos Endpoints da API REST

**MAPPER - Endpoints da API REST em DEV**

* **POST_MAP**
  * **POST** - https://05ovjshnib.execute-api.us-east-2.amazonaws.com/dev/core/mapper/map
   * **Descrição:** Endpoint dedicado ao mapeamento de um determinado payload conforme as regras estabelecidas pelo Template
   * **Parâmetros:**
     *  *body*:string (Body - Obrigatório) - O body é composto por 2 propriedades obrigatórias que são **config** e **payload**. A primeira é responsável por passar as informações relacionadas com o Template (*mapId*) e o tipo de origem do processo de mapeamento (*inputOrigin*). A segunda é responsável por armazenar o payload que efetivamente será convertido/mapeado conforme as regras estabelecidas no Template em questão. Existem 2 tipos de **inputOrigin**: **AWS_EVENT** e **DEFAULT**. O tipo **DEFAULT** é o padrão e serve para qualquer tipo de payload seja JSON ou XML, a raiz do documento em questão será referenciada dentro do Template em VTL pela propriedade **inputRoot**. No caso do tipo **AWS_EVENT**, esse é utilizado quando um evento recebido por um AWS Lambda deve ser lido e mapeado, nessa situação, mais propriedades estarão disponíveis dentro do Template VTL, quais sejam: **inputRoot**, **inputHeaders**, **inputQueryStringParameters**, **inputpathParameters** e **inputBody**.

        ```JSON
        {
            "config": {
                "mapId": map_id,
                "inputOrigin": "AWS_EVENT"
            },
            "payload": event
        }
        ```
    * **Retornos:**
      - **201**: Indica que o processo de mapeamento foi realizado com sucesso. No Header o campo **Content-Type** será definido como **text/xml** se o **outputType** do Template for XML ou **application/json**, caso contrário.
        - Corpo de retorno para o caso **outputType** igual a JSON:
          ```JSON
          {
            "requestId": string,
            "data": string
          }
          ```
        - Corpo de retorno para o caso **outputType** igual a XML:
          ```XML
          <?xml version="1.0" encoding="UTF-8"?>
          <nome_da_tag_raiz>
            ...
          </nome_da_tag_raiz>
          ```
      - **400**: Bad Request, indicando que não foi possivel realizar o processo de conversão com o mapId e o input fornecido.
        ```JSON
        {
          "status":400,
          "code":"BAD REQUEST",
          "title":"Bad Request",
          "detail":"Não foi possivel realizar o processo de conversão com o mapId e o input fornecido. Favor verificar o log e/ou contate o administrador do sistema."
        }
        ```
      - **403**: Forbidden, indicando que não foi possivel realizar o processo de conversão com o mapId fornecido por ele estar desativado.
        ```JSON
        {
            "requestId": requestID,
            "errors":[
                {
                    "status":403,
                    "code":"TEMPLATE NÃO ESTÁ ATIVO E NÃO PODE SER USADO",
                    "title":"Template de mapeamento não está ativo",
                    "detail":"O mapId informado corresponde a um template desativado."
                }
            ]
        }
        ```
      - **404**: O mapId informado não possui nenhum template associado.
        ```JSON
        {
          "status":404,
          "code":"TEMPLATE DE MAPEAMENTO NÃO ENCONTRADO",
          "title":"Template de mapeamento não encontrado",
          "detail":"O mapId informado não possui nenhum template associado."
        }
        ``` 
  

* **POST_MAPPER_TEMPLATE**
  * **POST** - https://05ovjshnib.execute-api.us-east-2.amazonaws.com/dev/core/mapper/template
   * **Descrição:** Insere um novo template na tabela **\<env>-mapper-dynamodb-table-templates**
   * **Parâmetros:**
     *  *body*:string (Body - Obrigatório) - O body é composto pelas propriedades abaixo:
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
        Adicionalmente durante o processo de inserção, as propriedades **mapId** (é um **UUID v4**), *templateVersions*, *insertionDate*, *updateDate* e *active* (*true* por padrão) serão adicionadas ao registro na tabela. Ressalta-se que o mapId será gerado automaticamente pelo endpoint.

    * **Retornos:**
      - **201**: Indica que o processo de inserção do template foi realizado com sucesso.
          ```JSON
          {
            "requestId": string,
            "data": {
                "mapId": string
            }
          }
          ```
      - **500**: Erro interno de servidor, indicando que não foi possivel realizar o processo de inserção do Template com os parâmetros fornecidos.
        ```JSON
        {
          "requestId": string,
          "errors":[
            {
              "status":500,
              "code":"INTERNAL SERVER ERROR",
              "title":"Erro Interno de Servidor",
              "detail":"Não foi possivel realizar a inserção do item. Favor verificar o log e/ou contate o administrador do sistema."
            }
          ]
        }
        ```

* **GET_MAPPER_TEMPLATE**
  * **GET** - https://05ovjshnib.execute-api.us-east-2.amazonaws.com/dev/core/mapper/template
   * **Descrição:** Retorna uma lista de Templates. Para realização da consulta, deve ser utilizado ao menos um dos seguintes parâmetros: **mapId**, **product**, **inputType**. O parâmetro **lastEvaluatedKey** deve ser sempre passado para garantir o processo de consulta paginada. O parâmetro **lastEvaluatedKey** sempre está presente nos retornos da página como resultado da consulta.
   * **Parâmetros:**
     *  *mapId*:string (Query - Opcional) - é o UUID que representa o template. Esse campo deve ser utilizado sempre que se quiser restringir a consulta buscando apenas o template com o mapId informado.
     *  *product*:string (Query - Opcional) - é a categoria de templates relacionados por produto (ex. pix).
     *  *subproduct*:string (Query - Opcional) - é a categoria de templates relacionados por subproduto (ex. post_dict_chave, post_mliq_entrada_tratarpix).
     *  *operation*:string (Query - Opcional) - é a categoria de templates relacionados por operação (ex. afr_mapping).
     *  *suboperation*:string (Query - Opcional) - é a categoria de templates relacionados por operação (ex. afr_mapping_risco_dict, afr_mapping_risco_mliq).
     *  *inputType*:string (Query - Opcional) - indica o tipo de input do payload [XML ou JSON].
     *  *outputType*:string (Query - Opcional) - indica o tipo de output do payload [XML ou JSON].
     *  *active*:string (Query - Opcional) - indica se o template está ativo ou não para realização de mapeamento.
     *  *size*:string (Query - Opcional) - tamanho da página a ser retornada. Default: 100.
     *  *lastEvaluatedKey*:string (Query - Opcional) - indica o valor da última chave retornada na página. Esse parâmetro é utilizado para se continuar o processo de paginação juntamente ao DynamoDB, caso não seja utilizado, a consulta sempre retornará a primeira página.

   * **Retornos:**
      - **200**: Indica que o processo de inserção do template foi realizado com sucesso.
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
      - **400**: Erro interno de servidor, indicando que não foi possivel realizar o processo de inserção do Template com os parâmetros fornecidos.
        ```JSON
        {
          "requestId":"a30ed1e4-de62-11eb-ba80-0242ac130004",
          "errors":[
            {
              "status":400,
              "code":"BAD REQUEST",
              "title":"Bad Request",
              "detail":"Para realização da consulta, utilize ao menos um dos seguintes parâmetros: mapId, product, inputType"
            }
          ]
        }
        ```

* **PATCH_MAPPER_TEMPLATE**
  * **PATCH** - https://05ovjshnib.execute-api.us-east-2.amazonaws.com/dev/core/mapper/template
   * **Descrição:** Atualiza um template da tabela **\<env>-mapper-dynamodb-table-templates**
   * **Parâmetros:**
     *  *body*:string (Body - Obrigatório) - O body é composto pelas propriedades abaixo:
        ```JSON
        {
          "mapId": string (campo Obrigatório),
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

    * **Retornos:**
      - **201**: Indica que o processo de inserção do template foi realizado com sucesso.
          ```JSON
          {
            "requestId": string,
            "data": {
                ...item inserido...
            }
          }
          ```
      - **400**: Bad Request, indicando que não foi possivel realizar o processo de atualização do Template com os parâmetros fornecidos.
        ```JSON
        {
          "requestId": string,
          "errors": [
            {
              "status":400,
              "code":"REQUISIÇÃO INVÁLIDA",
              "title":"Requisição Inválida",
              "detail":"O campo obrigatório mapId não foi encontrado no corpo da requisição."
            }
          ]
        }
        ```
      - **404**: NOT FOUND, indicando que não foi possivel realizar o processo de atualização do Template com os parâmetros fornecidos.
        ```JSON
        {
          "requestId": string,
          "errors": [
            {
              "status":404,
              "code":"MAPEAMENTO NÃO ENCONTRADO",
              "title":"Mapeamento não encontrado",
              "detail":"Não foi possível encontrar o mapeamento com o referido mapId."
            }
          ]
        }
        ```

## Utilização
Abaixo seguem exemplos dos 4 tipos de mapeamento permitidos para o Mapper:

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

  * **TEMPLATE DE EXEMPLO**
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
        "birthplace": "CAMPO NÃO EXISTE E NÃO SERÁ MOSTRADO",
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
  * **TEMPLATE DE EXEMPLO**
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
  * **TEMPLATE DE EXEMPLO**
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
  * **TEMPLATE DE EXEMPLO**
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
  * A função de macro **#validate(\$field, \<type>)** é uma macro criada para ser utilizada opcionalmente, mesmo estando disponível na ferramenta Mapper. A principal finalidade da função é evitar que retornos mal-processados pelo motor VTL existam no output (ex. string com código VTL ou blank). Recomenda-se, portanto, que a macro sempre seja utilizada. A função recebe como entrada 02 (dois) parâmetros: $field (que é o campo do input onde será lido o dado de entrada para ser validado) e \<type> que pode ser qualquer um dos tipos:
    * **"string"**: garante que o dado validado será retornado como string
    * **"number"**: garante que o dado validado será retornado como number
    * **"boolean"**: garante que o dado validado será retornado como boolean
    * **"object"**: garante que o dado validado será retornado sem nenhuma alteração em relação ao original

## FUNÇÕES CUSTOMIZADAS
  * Adicionalmente as funções básicas do motor VTL, a ferramenta Mapper disponibiliza ainda as seguintes funções de uso genérico:
    * **"string".substring(start, end)**: retorna uma substring de uma string dada passando como parâmetros os índices de início e fim. Ex.
      ```
      "countryCode": #validate($inputBody.txChave.substring(1, 3), "number")
      ```
    * **"string".contains(text)**: retorna um booleano indicando se uma determinada cadeia de caracteres está contida ou não em outra.
    * **"string".convert_timezone(from_tz, to_tz)**: converte um date_time de uma timezone, representado por uma string, em outro date_time de outra time_zone e retorma a nova representação no pattern **("%Y-%m-%dT%H:%M:%S.%fZ")**. Ex.
      ```
      "referenceDate": #validate($inputHeaders.timestamp.convert_timezone(0,0), "string")
      ```
    * **"string".get_date(str_time)**: extrai apenas a data de um date_time representado por uma string, o pattern da data final deve ser passado como parâmetro para a função. Ex.  
      ```
      "openingDate": #validate($inputBody.pix.dtPagto.get_date("%Y-%m-%dT00:00:00.000+00:00"), "string")
      ```
  * Além das funções básicas do motor VTL e as de uso genérico mencionadas acima, a ferramenta Mapper também disponibiliza funções de domínio de negócio. Caso seja necessário acrescentar mais funções desse tipo, uma implementação em código deverá ser realizada:
    * **"string".get_key_type(text)**: retorna o tipo de chave (PIX) de acordo com o texto de entrada, os retornos possíveis serão (EMAIL, PHONE, CPF, CNPJ, EVP ou uma string vazia, quando não existe correspondência). Ex.
      ```
      "type": #validate($inputBody.pix.txChaveRecebedor.get_key_type(), "string")
      ```