# Verificar y Aplicar Migraciones

El problema de que no se guarden los datos en la base de datos probablemente es porque **las migraciones no están aplicadas**.

## Paso 1: Verificar migraciones pendientes

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
python manage.py showmigrations
```

Busca la sección `encargado` y verifica si hay migraciones sin aplicar (aparecerán con `[ ]` en lugar de `[X]`).

## Paso 2: Aplicar migraciones

Si hay migraciones pendientes, ejecuta:

```bash
python manage.py migrate
```

Esto aplicará todas las migraciones pendientes a la base de datos.

## Paso 3: Verificar de nuevo

Después de migrar, vuelve a ejecutar:

```bash
python manage.py showmigrations
```

Todas las migraciones deben aparecer con `[X]`.

## Paso 4: Probar nuevamente

1. Crea un pedido pendiente
2. Inicia el pedido
3. Agrega un producto
4. Verifica en la consola si ves los mensajes DEBUG
5. Finaliza el pedido

Si aún no se guarda, copia los mensajes de error de la consola y dímelos.

## Alternativa: Ver errores en la consola

Mientras estés intentando agregar productos o finalizar pedidos, mira la consola del servidor Django. Allí deberías ver los mensajes DEBUG que indican si se está creando o si hay errores.
