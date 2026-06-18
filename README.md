# GastosFix - Sistema de Gestión Financiera Personal Premium

# Contexto General del Proyecto
GastosFix es una aplicación web robusta y una API REST desarrollada con el framework Flask, diseñada para resolver la necesidad de llevar un control detallado, seguro y categorizado de los gastos cotidianos. Este proyecto simula un entorno real de desarrollo, donde se interpreta una necesidad financiera y se construye una solución integrada desde cero utilizando persistencia en una base de datos relacional (MySQL).
# Tecnologías y Entorno de Desarrollo
    -Sistema Operativo:** Windows 11
    -Lenguaje:** Python 3.11+
    -Framework Web:** Flask 3.0.0
    -Base de Datos:** MySQL ( / phpMyAdmin local)
    -Conector:** mysql-connector-python 8.2.0
    -Diseño de Interfaz:** Bootstrap 5 con arquitectura Dark/Glassmorphism Premium
    -Herramienta de Pruebas de API:** Postman
# Arquitectura de Datos (Modelos Relacionados)
    -El sistema cumple estrictamente con el requisito de integrar al menos tres entidades relacionales mediante llaves foráneas (ForeignKeys):
    1. Gasto (Entidad Principal):** Contiene los campos `id`, `descripcion`, `monto`, `fecha`, `categoria_id` (FK) y `metodo_pago_id` (FK).
    2. Categoría:** Catálogo para clasificar el flujo (Ej: Alimentación, Transporte, Servicios).
    3. Método de Pago:** Canales utilizados para la transacción (Ej: Efectivo, Tarjeta de Crédito, Transferencia).
