# Guía de diseño y reporte

## Responsabilidades

- `Money` es un Value Object inmutable: representa un importe y una moneda, conserva precisión decimal y valida su valor al construirse.
- `Customer` contiene identidad y banderas de membresía y actividad.
- `OrderItem` representa un SKU, cantidad y precio unitario; calcula el subtotal.
- `Order` es el Aggregate Root. Protege el límite de unidades, la confirmación y el ciclo de vida.
- `Specification` encapsula una condición que se puede probar por separado y combinar con `&`, `|` y `~`.
- `DiscountPolicy` combina las reglas de 10 % y 5 % con OR (`any_discount`) y, si ambas aplican, da prioridad al 10 %. Las Specifications no modifican pedidos.
- `DomainEvent` registra un hecho después de una transición válida. Cada evento incluye identificador del pedido y fecha/hora UTC.
- `app.api` recibe HTTP, delega en `Order` y traduce errores del dominio a códigos HTTP.

## Preguntas del reporte

**¿Por qué se usa Decimal en lugar de float para precios?**

`Decimal` representa cantidades decimales de forma exacta para los importes del CSV. Un `float` usa representación binaria y operaciones de dinero pueden acumular aproximaciones. El modelo rechaza `float` para evitar introducir esos valores en `Money`.

**¿Cuál es la diferencia entre contar renglones y sumar unidades?**

Un renglón representa un SKU, mientras que su cantidad puede ser mayor que uno. O009, por ejemplo, tiene un renglón con 19 unidades. El máximo de 20 se valida con la suma de `quantity` de todos los artículos.

**¿Qué ventaja tiene encapsular una regla en Specification?**

La condición obtiene un nombre, se puede probar aisladamente y se reutiliza en una composición. En este proyecto, el descuento del 10% combina monto, VIP, unidades y ausencia de promoción mediante AND y NOT; la regla de 5 % se une a la de 10 % con OR en `DiscountPolicy.any_discount`.

**¿Por qué los eventos se registran solo después de una transición válida?**

Un evento afirma que algo sucedió. Primero se valida la operación, luego se actualiza el estado y finalmente se registra el evento. E11 demuestra que un envío sin guía no agrega `OrderShipped`.

**¿Qué parte se podría reutilizar si se reemplaza FastAPI por otra interfaz?**

Las entidades, Value Objects, Specifications, política de descuentos, excepciones y transiciones del dominio. Una interfaz distinta llamaría los mismos métodos de `Order` y traduciría sus resultados a su propio protocolo.

## Reflexión para personalizar

La siguiente reflexión es una base técnica; conviene que el estudiante la ajuste a los problemas que observó en su propia ejecución:

> Al revisar la actividad, identifiqué tres riesgos: usar `float` para dinero, limitar la cantidad de renglones en lugar de las unidades y registrar un evento antes de validar completamente una transición. Los resolví usando `Decimal`, sumando las cantidades de cada OrderItem y registrando eventos solo después de actualizar el estado. Aprendí que las reglas deben vivir en el dominio para que una llamada de API y una prueba obtengan el mismo comportamiento.

## Guía de estados y Domain Events

| Estado inicial | Operación | Estado final | Evento |
| --- | --- | --- | --- |
| DRAFT | `confirm()` | CONFIRMED | OrderConfirmed |
| CONFIRMED | `ship(guía)` | SHIPPED | OrderShipped |
| CONFIRMED | `cancel(motivo)` | CANCELLED | OrderCancelled |
| SHIPPED | `deliver()` | DELIVERED | OrderDelivered |
| SHIPPED | `return_order()` | RETURNED | OrderReturned |

Los estados no listados como transición válida se rechazan sin cambiar el pedido ni su historial de eventos. `ship()` requiere guía no vacía; `cancel()` requiere motivo no vacío.
