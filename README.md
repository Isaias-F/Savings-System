# Savings-System

Este proyecto personal fue enfocado para llevar un mejor control con el dinero.
Inició como un sistema de cajero automático y agregué varias funciones adicionales entre ellas:

- Crear cuenta con ID automático e irrepetible, tipo de cuenta, más registro de PIN
- Depósito
- Retiro
- Ver cuentas registradas
- Ver cantidad guardada
- Modificar datos
- Borrar cuenta
- Ver historial de transacciones
- Exportar hsitorial de transacciones en PDF

### Reportes

El historial de reportes es un sistema simple que obtiene los movimientos realizados al mes anterior del mes actual.
Mostrando:
- ID de transacción
- Tipo de transacción
- Fecha
- Cantidad

Todo esto adjuntando al número de cuenta y mostrando una gráfica para mostrar el porcentaje de las operaciones realizadas en todo el mes anterior.

### Características adicionales

Incluye la función de bloquear cuenta si el PIN de seguridad es introducido de forma erronea más de 3 veces, al exceder el límite, la cuenta se bloquea, y es necesario acceder a la base de datos para el debloqueo de la misma.
