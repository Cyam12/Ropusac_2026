# ROPUSAC

Sistema web desarrollado para la gestión de usuarios, proveedores, clientes, productos, precios de venta, cotizaciones, ventas y boletas electrónicas.

## Tecnologías

- Python
- Flask
- PostgreSQL
- SQLAlchemy
- Flask-Migrate / Alembic
- Bootstrap
- Render
- Neon PostgreSQL

---

# RESUMEN

### Si desean aplicar cambios y utilizar la base de datos actual

```text
Clonar proyecto
      ↓
pip install -r requirements.txt
      ↓
Crear .env
      ↓
Solicitar DATABASE_URL
      ↓
Configurar APIs
      ↓
flask run
```
CUANDO CONSIDEREN QUE SU INTEGRACION ESTE CORRECTA SUBEN SUS CAMBIOS AL REPOSITORIO para que se actualice el proyecto en RENDER

### Si desean usar una base completamente limpia

```text
Clonar proyecto
      ↓
pip install -r requirements.txt
      ↓
Crear PostgreSQL
      ↓
Crear .env
      ↓
Configurar DATABASE_URL
      ↓
Configurar APIs
      ↓
flask --app run.py db upgrade
      ↓
flask crear-administrador
      ↓
flask run
```

---

# Recomendaciones si trabajar de forma local con la Base de Datos de NEON

- Antes de crear una migración nueva, revisar las migraciones existentes (solo si requieren hacerlo).
- No eliminar migraciones que ya hayan sido aplicadas.
- No modificar directamente una migración que ya haya sido utilizada en producción.
- Para nuevas modificaciones de base de datos, crear una migración adicional.
- Si trabajan con la base principal, recordar que los registros creados localmente también quedarán registrados allí.

# Recomendaciones antes de subir a Github sus nuevos cambios
- No subir `.env` al repositorio.
- No compartir públicamente `DATABASE_URL`.
- No compartir API Keys.
---

# POR SI SE PIERDEN Y LES GUSTA LEER :v

## Apartir de aca esta mas detallado:
## Despliegue actual

Actualmente el proyecto se encuentra desplegado de la siguiente manera:

- **Aplicación:** Render
- **Base de datos:** Neon PostgreSQL

---

# FORMA 1. Ejecutar el proyecto localmente usando la base de datos actual

Esta es la opción más sencilla si solamente desean modificar o probar el proyecto.

## Paso 1. Descargar o clonar el proyecto

Ingresar a la carpeta principal del proyecto desde la terminal.

Ejemplo:

```bash
cd ROPUSAC
```

---

## Paso 2. Instalar las dependencias

Si todavía no tienen instaladas las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

---

## Paso 3. Crear el archivo `.env`

En el proyecto encontrarán:

```text
.env.example
```

Crear una copia y renombrarla como:

```text
.env
```

El archivo `.env` contiene las variables necesarias para ejecutar el sistema.

Por ejemplo:

```env
DATABASE_URL=
```


También deberán configurar las API Keys y demás credenciales indicadas en `.env.example`.
> PARA ELLO DEBEN CREARSE UNA CUENTA EN ESOS SERVICIOS PARA QUE GENEREN LOS TOCKENS

> No subir el archivo `.env` al repositorio porque contiene credenciales privadas.

---

## Paso 4. Solicitar el `DATABASE_URL`

Si desean trabajar utilizando la base de datos actual del proyecto, deben solicitarme el `DATABASE_URL` correspondiente.

Colocarlo dentro de:

```env
DATABASE_URL=URL_DE_LA_BASE_DE_DATOS
```



## Paso 5. Verificar las migraciones

El proyecto actualmente cuenta con las siguientes migraciones:

```text
0001_baseline_ropusac.py
0002_stock_productos.py
0003_indices_vendedor.py
```

Pueden verificar el estado de la base de datos con:

```bash
flask --app run.py db current
```

Para verificar cuál es la última migración disponible:

```bash
flask --app run.py db heads
```

Actualmente la última migración debe ser:

```text
0003_indices_vendedor
```

---

## Paso 7. Ejecutar el proyecto

```bash
flask run
```

Luego ingresar desde el navegador a la dirección mostrada en la terminal, normalmente:

```text
http://127.0.0.1:5000
```

---

# IMPORTANTE AL USAR LA BASE DE DATOS DEL PROYECTO

Si utilizan el `DATABASE_URL` de la base de datos principal, estarán conectándose directamente a la base utilizada por el proyecto.

Esto significa que cualquier registro que creen desde su entorno local, por ejemplo:

- usuarios,
- proveedores,
- clientes,
- productos,
- cotizaciones,
- ventas,
- boletas,

será almacenado en esa misma base de datos.

Por ese motivo, evitar eliminar o modificar información importante cuando estén realizando pruebas.

---

# FORMA 2. Crear una base de datos limpia

Si desean trabajar sin modificar la base de datos principal, pueden crear su propia base PostgreSQL.

Pueden utilizar, por ejemplo:

- Neon
- Render PostgreSQL
- PostgreSQL instalado localmente
- Otro proveedor compatible con PostgreSQL

---

## Paso 1. Crear la base PostgreSQL

Crear una base de datos nueva en la plataforma elegida.

Una vez creada, obtener su cadena de conexión o `DATABASE_URL`.

Ejemplo:

```text
postgresql://usuario:contraseña@servidor/base_datos
```

---

## Paso 2. Configurar `.env`

Colocar la nueva conexión:

```env
DATABASE_URL=URL_DE_SU_BASE_DE_DATOS
```

Completar también las demás variables necesarias indicadas en:

Si son servicios de API crearse una cuenta en esos servicios para la generacion de los TOKEN

```text
.env.example
```

---

## Paso 3. Crear toda la estructura de la base

No es necesario ejecutar los archivos SQL manualmente.

Para crear la estructura utilizando las migraciones existentes solamente ejecutar:

```bash
flask --app run.py db upgrade
```

Flask-Migrate aplicará automáticamente las migraciones en orden:

```text
0001_baseline_ropusac
        ↓
0002_stock_productos
        ↓
0003_indices_vendedor
```

Al finalizar, la base de datos tendrá la estructura necesaria para ejecutar el proyecto.

---

## Paso 4. Verificar la migración

Ejecutar:

```bash
flask --app run.py db current
```

Debería aparecer:

```text
0003_indices_vendedor
```

## Paso 5. Crear el primer administrador

Como la base estará vacía, crear el primer usuario administrador desde la terminal:

```bash
flask crear-administrador
```

El sistema solicitará los datos necesarios para crear el usuario.

Guardar las credenciales porque serán utilizadas para iniciar sesión.

---

## Paso 6. Ejecutar Flask

```bash
flask run
```

Luego ingresar a:

```text
http://127.0.0.1:5000
```

Iniciar sesión con el administrador creado anteriormente.

En este momento tendrán una base de datos independiente y podrán comenzar a registrar información desde cero.

---

# 5. APIs y servicios externos

El sistema utiliza diferentes servicios externos.

Las variables necesarias se encuentran documentadas en:

```text
.env.example
```

Antes de ejecutar todas las funcionalidades del proyecto deberán configurar las credenciales correspondientes.

Nunca colocar API Keys directamente dentro del código Python.

Utilizar siempre variables de entorno mediante:

```text
.env
```

---

# 6. Comandos rápidos

## Primera instalación

```bash
pip install -r requirements.txt
```

Crear:

```text
.env
```

Luego:

```bash
flask --app run.py db upgrade
```

Si es una base nueva:

```bash
flask crear-administrador
```

Finalmente:

```bash
flask run
```

---

## Para trabajar normalmente

```bash
flask run
```

> GRACIAS POR LEER :D