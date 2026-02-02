# Guía de Prueba - Flujo de Pedidos

## Resumen de Cambios Implementados

### 1. **Vista `iniciar_pedido`** ✅

- **Problema:** Usaba `get_or_create` sin identificador único, causando error `MultipleObjectsReturned`
- **Solución:** Ahora obtiene el pedido más reciente del cliente o crea uno nuevo
- **Mejoras:**
  - Guarda `pedido_pendiente_id` en sesión
  - Pasa lista de productos disponibles al template
  - Valida que el pedido_pendiente exista

### 2. **Vista `agregar_producto_por_id`** ✅

- **Mejoras:**
  - Valida que exista `pedido_pendiente_id` en sesión
  - Mejor manejo de errores cuando el producto no existe
  - Mensajes más claros

### 3. **Vista `eliminar_producto_pedido`** ✅

- **Mejoras:**
  - Obtiene `pedido_pendiente_id` de sesión correctamente
  - Redirige al pedido_pendiente después de eliminar

### 4. **Vista `cancelar_pedido`** ✅

- **Cambios:**
  - Ahora elimina el `pedido_pendiente` junto con el `pedido`
  - Limpia ambas variables de sesión
  - Mensajes mejorados

### 5. **Vista `finalizar_pedido`** ✅

- **Cambios:**
  - Valida que el pedido tenga productos antes de permitir acceso
  - Carga formulario para completar datos (comercio_origen, observaciones)
  - Elimina el `pedido_pendiente` al finalizar
  - Limpia sesión correctamente

### 6. **Template `iniciar_pedido.html`** ✅

- **Nuevas características:**
  - Diseño mejorado con tarjetas (cards)
  - Información del cliente visible
  - Tabla de productos agregados con más detalles
  - **Botones agregados:**
    - Volver
    - Cancelar Pedido (con confirmación)
    - Finalizar Pedido (deshabilitado sin productos)

### 7. **Template `finalizar_pedido.html`** ✅

- **Nuevo archivo creado para:**
  - Resumen del pedido
  - Lista de productos
  - Formulario para completar datos
  - Botones de acción (Volver, Finalizar)

## Flujo Completo de Pedidos

```
1. Usuario en "Pedidos Pendientes" → Hace clic en "Iniciar Pedido"
   ↓
2. Se carga `iniciar_pedido` con:
   - Información del cliente
   - Formulario para agregar productos
   - Lista de productos agregados
   - Botones: Volver, Cancelar, Finalizar
   ↓
3. Usuario puede:
   a) Agregar productos
      - Valida que no se dupliquen
      - Actualiza la lista
   b) Eliminar productos
      - Remueve del detalle
      - Actualiza la lista
   c) Cancelar pedido
      - Elimina pedido y pedido_pendiente
      - Vuelve a pendientes
   d) Finalizar (si hay productos)
      - Va a `finalizar_pedido`
   ↓
4. En `finalizar_pedido`:
   - Selecciona sucursal origen
   - Agrega observaciones
   - Hace clic en "Finalizar"
   ↓
5. Sistema:
   - Guarda datos del pedido
   - Elimina pedido_pendiente
   - Limpia sesión
   - Redirige a "Pedidos Pendientes"
```

## Checklist de Pruebas

- [ ] Acceder a un pedido pendiente sin error
- [ ] Ver información del cliente correctamente
- [ ] Agregar un producto al pedido
- [ ] No poder duplicar productos
- [ ] Eliminar un producto del pedido
- [ ] Cancelar pedido (verificar que se elimina pedido_pendiente)
- [ ] Finalizar pedido sin productos (debe mostrar error)
- [ ] Finalizar pedido con productos (debe mostrar formulario)
- [ ] Completar datos y finalizar
- [ ] Verificar que pedido_pendiente se eliminó
- [ ] Verificar que sesión se limpió

## Notas Técnicas

- `pedido_pendiente_id` se guarda en sesión para poder regresar
- `pedido` se crea una sola vez por cliente (estado=1)
- Al finalizar, se limpia sesión y se elimina pedido_pendiente
- Validaciones en frontend y backend
