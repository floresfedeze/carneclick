#  ![image alt](https://github.com/floresfedeze/carneclick/blob/6a8f8d9733be6d971fa426c61fc8474107fda4a8/carneclick/static/img/supercarnes1%20(1).png)
Sistema web desarrollado en Django para la gestión de productos cárnicos y administración básica de una carnicería o comercio del rubro alimenticio.

Proyecto realizado para **Práctica Profesional I**.

---

### Descripción

*CarneClick* es una aplicación web que permite administrar un comercio cárnico desde el navegador, centralizando productos, usuarios y operaciones en un solo sistema.

El objetivo principal es simplificar la gestión diaria del negocio mediante una interfaz clara, intuitiva y funcional.

---

### Funcionalidades

- Gestión de productos cárnicos
- Administración de usuarios
- Panel de administración con Django
- Base de datos integrada (SQLite)
- Sistema de autenticación
- Interfaz responsive con Bootstrap
- Protección CSRF integrada

---

### Tecnologías Utilizadas
[![My Skills](https://skillicons.dev/icons?i=js,html,css,py,sqlite,django,bootstrap)](https://skillicons.dev)

---

#### Requisitos 



###### - Python 3 instalado
###### - Conexión a internet
###### - Navegador web
###### - Git (opcional)

---

## Instalación Completa desde Cero

Guía explicada paso a paso como si la computadora no tuviera nada instalado.

---

### 1. Instalar Python

1. Ir a https://www.python.org/downloads/
2. Descargar Python 3.
3. Durante la instalación marcar la opción:

   ✔ Add Python to PATH

4. Verificar instalación:

```bash
python --version
```

Si aparece algo como `Python 3.x.x`, está correctamente instalado.

---

### 2. Descargar el Proyecto

Clonar el repositorio:

```bash
git clone https://github.com/floresfedeze/carneclick.git
```

O descargar el ZIP desde GitHub y descomprimirlo.

Entrar en la carpeta del proyecto:

```bash
cd carneclick
```

---

### 3. Crear Entorno Virtual

```bash
python -m venv venv
```

Activar entorno virtual:

##### Windows
```bash
venv\Scripts\activate
```

##### Linux / Mac
```bash
source venv/bin/activate
```

Si aparece `(venv)` en la terminal, está funcionando correctamente.

---

### 4. Instalar Dependencias

```bash
pip install -r requirements.txt
```

---


### 5. Migrar la Base de Datos

Ejecutar los siguientes comandos:

```bash
python manage.py makemigrations
python manage.py migrate
```

Esto crea automáticamente la base de datos SQLite.

---

#### 6. Crear Usuario Administrador

```bash
python manage.py createsuperuser
```

Completar:

- Usuario
- Email
- Contraseña

---

### 7. Ejecutar el Servidor

```bash
python manage.py runserver
```

El sistema estará disponible en:

```
http://127.0.0.1:8000/
```

Panel administrador:

```
http://127.0.0.1:8000/admin
```

---



# Tipos de Usuario

## Administrador
- Control total del sistema
- Acceso al panel `/admin`

## Encargado
- Gestión y actualización de productos.
- Control y seguimiento del stock.

---

## Cliente
- Visualización de productos disponibles.
- Gestión de su información personal.


---

#  Estructura General del Proyecto

```
carneclick/
│
├── .vscode
├── administrador
├── carneclick
├── cliente
├── encargado
├── pdf
├── README.md
├── db.sqlite3
├── manage.py
├── requirements.txt
```

---

# 🎯 Objetivo Académico

Proyecto desarrollado como práctica profesional aplicando:

- Desarrollo Backend con Django
- Gestión de bases de datos
- Estructuración de proyectos web
- Configuración de entornos virtuales
- Implementación de medidas básicas de seguridad

---

# 👨‍💻 Autor

**Federico Ezequiel Flores**  
Desarrollador del sistema CarneClick
