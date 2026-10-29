# Bitácora de escenarios E01–E15

Cada caso se ejecutó con una carga nueva de `load_fixture()`. Así, las transiciones de un escenario no alteran las precondiciones del siguiente. Los estados, resultados y eventos de esta bitácora corresponden a la ejecución de `python -m app.scenarios`; las pruebas parametrizadas de `tests/test_scenarios.py` comprueban los 15 resultados.

| Caso | Estado inicial | Precondiciones | Operación | Resultado observado | Evento | Prueba |
| --- | --- | --- | --- | --- | --- | --- |
| E01 | DRAFT | O001 está DRAFT; cliente VIP activo; 4 unidades; 2100.00 MXN; sin promoción. | Evaluar descuento. | 10%. Cumple las cuatro condiciones AND. | Ninguno; evaluar no cambia el pedido. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E01]` |
| E02 | DRAFT | O002 está DRAFT; cliente no VIP activo; 2 unidades; 1050.00 MXN; sin promoción. | Evaluar descuento. | 0%. No cumple el requisito VIP ni el umbral alternativo de 5000 MXN. | Ninguno. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E02]` |
| E03 | DRAFT | O003 está DRAFT; cliente VIP pero inactivo; 4 unidades; 2100.00 MXN. | Confirmar. | Rechazo `InvalidOrderData`; queda DRAFT. | Ninguno: no ocurrió transición. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E03]` |
| E04 | DRAFT | O005 está DRAFT; cliente VIP activo; 4 unidades; 2100.00 MXN; promoción activa. | Evaluar descuento. | 0%; la promoción excluye ambas reglas. | Ninguno. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E04]` |
| E05 | DRAFT | O006 está DRAFT; cliente activo no VIP; 1 unidad; 18000.00 MXN; sin promoción. | Evaluar descuento. | 5%; el total supera 5000 MXN. | Ninguno. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E05]` |
| E06 | DRAFT | O007 está DRAFT, pertenece a un cliente activo y no tiene artículos. | Confirmar. | Rechazo `InvalidOrderData`; queda DRAFT. | Ninguno. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E06]` |
| E07 | DRAFT | O008 está DRAFT; cliente activo; suma exactamente 20 unidades; 2400.00 MXN. | Confirmar. | Éxito; estado CONFIRMED. El límite incluye 20 unidades. | `OrderConfirmed`. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E07]` |
| E08 | DRAFT | O009 está DRAFT con 19 unidades y total 2280.00 MXN. | Agregar SKU003 × 2. | Rechazo `OrderItemLimitExceeded`; sigue con 19 unidades en DRAFT. La lista no se modifica. | Ninguno. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E08]` |
| E09 | DRAFT | O010 está DRAFT; total exactamente 500.00 MXN; 2 unidades; cliente activo no VIP. | Evaluar descuento. | 0%; el umbral usa `> 500`, no `>= 500`. | Ninguno. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E09]` |
| E10 | DRAFT | O011 está DRAFT; cliente VIP activo; total 1500.00 MXN; 3 unidades; sin promoción. | Evaluar descuento. | 0%; faltan unidades para llegar al mínimo de 4. | Ninguno. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E10]` |
| E11 | DRAFT | O012 está DRAFT; cliente activo; 1 unidad; 850.00 MXN. | Confirmar y luego intentar enviar con guía en blanco. | La confirmación sí se completa; el envío se rechaza con `InvalidOrderData`. Termina CONFIRMED. | Solo `OrderConfirmed`; no se agrega `OrderShipped`. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E11]` |
| E12 | DRAFT | O013 está DRAFT; cliente activo; 1 unidad; 600.00 MXN. | Confirmar dos veces. | Primera confirmación válida; la segunda rechaza con `InvalidOrderTransition`. Termina CONFIRMED. | Un solo `OrderConfirmed`. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E12]` |
| E13 | DRAFT | O014 está DRAFT; cliente activo; 1 unidad; 600.00 MXN. | Confirmar, enviar con `GUIA-O014` e intentar cancelar. | Confirmación y envío válidos; cancelar desde SHIPPED se rechaza con `InvalidOrderTransition`. Termina SHIPPED. | `OrderConfirmed`, `OrderShipped`; no `OrderCancelled`. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E13]` |
| E14 | DRAFT | O015 está DRAFT; cliente activo; 1 unidad; 450.00 MXN. | Confirmar, enviar con `GUIA-O015` y devolver. | Éxito; estado final RETURNED. | `OrderConfirmed`, `OrderShipped`, `OrderReturned`. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E14]` |
| E15 | DRAFT | O016 está DRAFT; cliente activo; 1 unidad; 2100.00 MXN. | Confirmar, enviar con `GUIA-O016` y entregar. | Éxito; estado final DELIVERED. | `OrderConfirmed`, `OrderShipped`, `OrderDelivered`. | `tests/test_scenarios.py::test_escenarios_e01_a_e15[E15]` |

## Resultado de la corrida

La salida completa queda en `evidencias/escenarios.txt`. La prueba de cada fila se repite de forma independiente con `pytest`, recargando los fixtures y comprobando resultado, estado final y secuencia exacta de eventos.
