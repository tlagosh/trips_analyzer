# trips_analyzer
Solución challenge de analisis de viajes, proceso de selección para Backend Developer en NeuralWorks, 2023.
- Se implementa una api en Flask con python 3 para satisfacer los requerimientos del problema en cuestión. Se utiliza sqlalchemy como ORM.
- La solución incluye algoritmos de clustering para la agrupación de viajes.

## Instalación

### Local

Para correr la api en local se debe hacer el setup de una base de datos local en postgresql. Luego, editar en .env.dev la variable de entorno DATABASE_URL

```
DATABASE_URL=postgresql://username:password@db:5432/trip_analyzer
```

Además, es necesario crear la database "trip_analyzer" en postgresql local.

### Docker

Se implementa docker compose en el proyecto. Para correr el contenedor se necesita instalar docker y luego ejecutar el comando:

```
docker-compose up -d --build
```

en el root del proyecto. Esto levantará un container para la api y uno llamado "db" para la base de datos. Además de inicializar y ejecutar ambas cosas.

## Items del problema propuesto y documentación

### 1. Procesos automatizados para ingerir y almacenar los datos bajo demanda
Se implementan 3 endpoints para solucionar este caso.
#### Post viaje

El primero es un endpoint que permite hacer un post de un viaje.

```
  POST /viajes
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `region` | `string` | **Required**. Región |
| `origin_lat` | `string` | **Required**. latitud de origen |
| `origin_lon` | `string` | **Required**. longitud de origen |
| `destination_lat` | `string` | **Required**. latitud de destino |
| `destination_lon` | `string` | **Required**. longitud de destino |
| `datetime` | `string` | **Required**. Datetime en formato "2019-01-18 08:25:29" |
| `datasource` | `string` | **Required**. la fuente de la data |

Este endpoit, además de crear el viaje, asigna los atributos de cluster de este viaje al viaje más cercano en términos de origen, destino y hora respectivamente. Esta implementacióon se hace de esta manera para no tener que correr el algoritmo de clustering completo cada vez que un viaje es agregado al sistema. La idea es usar el endpoint de clustering de manera periódica y controlada. Se explica en más detalle en las secciones siguientes.

#### Post para varios viajes
Se implementa también un endpoint que permite agregar al sistema varios viajes al mismo tiempo en formato de lista.

```
  POST /viajes/bulk
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `viajes`      | `list` | **Required**. Lista de los viajes a agragar |

#### a) Los viajes que son similares en términos de origen, destino y hora del día deben agruparse. Describa el enfoque que utilizó para agregar viajes similares.

Para solucionar este problema se implemento un algoritmo de clustering DBSCAN. Este algoritmo define 3 parametros adicionales de cada viaje:

| origin_cluster_id | destination_cluster_id | hour_cluster_id |
| :-------- | :------- | :-------------------------------- |

Estos parametros son enteros que nos ayudarán a agrupar los viajes según estas 3 dimensiones. La premiza es que, luego de hacer el clustering, 2 viajes con el mismo valor de "origin_cluster_id", por ejemplo, pertenecerían al mismo grupo según sus coordenadas de origen. Si alguno de estos atributos tiene valor "-1", significa que ese viaje (en esa dimensión) no pertenece a ningún cluster. Lo anterior es útil para identificar viajes "raros". De esta misma manera, si dos viajes tienen los 3 id de cluster iguales, significa que pertenecen al mismo grupo en todas las dimensiones, lo que nos está diciendo que son viajes muy similares.

#### Put para ejecutar clustering
Se implementa un endpoint que permite ejecutar el clustering para todos los viajes presentes en el sistema. El clustering se ejecuta por Region, dado que es una variable ya conocida que ayuda a que el algoritmo arroje mejores resultados.

```
  PUT /clusterize
```

Este endpoint no recibe parametros. Se elige el algoritmo DBSCAN principalmente porque permite hacer clustering sin saber previamente el número de clusters que se tienen. Lo anterior permite adecuarse a cualquier número de grupos presente en los viajes en la realidad. El algoritmo arrojó muy buenos resultados en las pruebas, pudiendo identificar perfectamente grupos en los viajes.

### 2. Otros servicios

#### Get promedio semanal
Se implementa también un endpoint que permite obtener el promedio semanal de el número de viajes dados ciertos parámetros.

```
  GET /weekmean
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `region` | `string` | **Required**. Región |
| `max_lat` | `string` | **Required**. latitud máxima |
| `max_lon` | `string` | **Required**. longitud máxima |
| `min_lat` | `string` | **Required**. latitud mínima |
| `min_lon` | `string` | **Required**. longitud mínima |
| `min_date` | `string` | **Required**. Datetime mínimo en formato "2019-01-18 08:25:29" |
| `max_date` | `string` | **Required**. Datetime máximo en formato "2019-01-18 08:25:29" |

#### Get health status
Se implementa también un endpoint que permite obtener estado de 3 de los servicios de la api, incluida la ingesta de datos.

```
  GET /health
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `servicio` | `string` | **Required**. servicio del que se quiere saber el estado.|

Los valores posibles de la variable servicio son "data_ingestion", "weekmean" y "clusterize". Lo anterior según de qué servicio se quiera saber el estado. La solución no utiliza pulling, ya que las variables de status están guardadas en base de datos, y se actualizan en base a eventos cuando los distintos servicios son utilizados, según si es que fallaron o no.

## Consideraciones generales

### Escalabilidad
La solución se prueba con 500 mil viajes y funciona de manera correcta. Se espera que pueda funcionar para el caso de 100 millones de viajes por las tecnologías utilizadas. La única preocupación en este sentido es los tiempos de ejecución del clustering en grandes cantidades de data, de este problema se habla más adelante en la sección de posibles mejoras.

### Documentación y pruebas

Se implementó una colección de pruebas en la plataforma postman. Con esta colección puede ser más fácil probar los distintos endpoints de la api. Se deja el link de esta colección.

[![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/16230990-4811b7c3-7179-471d-bf25-97020845e96c?action=collection%2Ffork&source=rip_markdown&collection-url=entityId%3D16230990-4811b7c3-7179-471d-bf25-97020845e96c%26entityType%3Dcollection%26workspaceId%3D97e3f7de-18fc-4d08-a932-e9c276cc694c)

### GCP

Para hacer el deploy de esta api a GCP, habría que subir la imagen del container a un servicio cloud. Para esto se puede ingresar al Google Cloud, apretar "crear servicio" y seleccionar la imagen del container, que tenemos que tener subida. Una vez terminada la configuración podemos agregar contenedores de gunicorn, nginx para manejar el balanceo de la api, además de otras funcionalidades de seguridad y escalabilidad presentes en GCP

### Archivos adicionales

Además de la api, este repositorio cuenta con los archivos:

- ```data_generator.py``` : script de python para generar un lista json con instancias de viajes. Está hecho para que genere viajes con atributos de origen, destino y hora con distribuciones normales. De esta manera se puede probar el clustering.
- ```csvfile_to_json_instances.py``` : script de python que lee un archivo csv con viajes como el entregado en la solución, y los pasa a un json legible por la api.
- ```autogenerated_instances.json``` : 100 mil instancias generadas por el data generator.
- ```instances.json``` : json de viajes entregados en el problema.
- ```trips.csv``` : Archivo original con viajes entregado en el problema.
- ```autogenerated_trips.csv``` : 100 mil instancias generadas por el data generator y guardadas en formato csv.
- ```.gitignore``` : git ignore para excluir archivos grandes de git.

### Posibles mejoras

#### Escalabilidad
* En las pruebas se puede ver que el tiempo del clustering sigue dependiendo de manera lineal de la cantidad de viajes presentes en el sistema. Si bien se implementa un algoritmo relativamente rápido, al momento de pensar en más de 1 millon de viajes los tiempos de clustering pueden comenzar a subir mucho. Para esto se proponen 3 posibles mejoras:
    - En primer lugar, se puede paralelizar mejor el clustering usando threading o multithread en python, o usando directamente las opciones de la librería sklearn.
    - En segundo lugar, se puede implementar procesos automatizados en el backgroud (workers) que corran la clusterización. También se puede aplicar lo mismo al algoritmo que asigna nuevos viajes a un cluster, para poder responder más rápido en el endpoint POST /viajes y asignar clusters luego.
    - Por último, se podría mejorar el proceso de búsqueda de el viaje más similar al momento de agregar un nuevo viaje. Este proceso es necesario ya que queremos poder definir los ids de cluster de este nuevo viaje sin tener que correr el cluestering general de todo el sistema. Para mejorar este proceso se pueden implementar relajaciones de la búsqueda (no buscar específicamente el más cercano, sino que uno suficientemente cercano, siguiendo ciertos parámetros).

#### Diseño de la solución
- Considerando que la solución se diseñó y programó en tan poco tiempo, le falta mucho para poder ser llevada a producción. En particular creo que son importantes los siguientes puntos:
    - Testing de la api y sus componentes.
    - Prácticas de devops, ci, cd.
    - Políticas de seguridad de endpoints con bearer token.
    - Respuestas de la api: Manejo de errores y código de respuesta en cada endpoint.

    Además de muchas otras cosas para asegurar el deploy seguro y exitoso a producción.


