import boto3
import hashlib
import json
import os
import pymysql

def insert_reader(event, context):
    # Leitura dos dados da requisição
    leitor_id = event['leitor_id']
    token = event['token']

    # Conexão com o banco de dados
    secretsmanager = boto3.client('secretsmanager')
    response = secretsmanager.get_secret_value(SecretId=f'replenish4me-db-password-{os.environ.get("env", "dev")}')
    db_password = response['SecretString']
    rds = boto3.client('rds')
    response = rds.describe_db_instances(DBInstanceIdentifier=f'replenish4medatabase{os.environ.get("env", "dev")}')
    endpoint = response['DBInstances'][0]['Endpoint']['Address']
    # Conexão com o banco de dados
    with pymysql.connect(
        host=endpoint,
        user='admin',
        password=db_password,
        database='replenish4me'
    ) as conn:

        # Verificação da sessão ativa no banco de dados
        with conn.cursor() as cursor:
            sql = "SELECT usuario_id FROM SessoesAtivas WHERE id = %s"
            cursor.execute(sql, (token,))
            result = cursor.fetchone()

            if result is None:
                response = {
                    "statusCode": 401,
                    "body": json.dumps({"message": "Sessão inválida"})
                }
                return response

            usuario_id = result[0]

            # Cálculo do hash do leitor_id e usuario_id
            hash_str = f"{leitor_id}:{usuario_id}"
            hash_object = hashlib.sha256(hash_str.encode())
            hash_hex = hash_object.hexdigest()

            # Inserção do registro na tabela Leitores
            sql = "INSERT INTO Leitores (id, usuario_id) VALUES (%s, %s)"
            cursor.execute(sql, (hash_hex, usuario_id))
            conn.commit()

    # Retorno da resposta da função
    response = {
        "statusCode": 200,
        "body": json.dumps({"message": "Leitor cadastrado com sucesso"})
    }
    return response
