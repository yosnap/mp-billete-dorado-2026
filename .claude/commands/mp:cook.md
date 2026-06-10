Activa el skill `mp:cook` para ejecutar un plan o fase de implementación.

Pasos a seguir:

1. Lee y carga el skill desde `.claude/skills/cook/SKILL.md`
2. Ejecuta el flujo completo del skill:
   - Carga la fase: usa `$ARGUMENTS` si se pasó una ruta, si no lista los planes disponibles
   - Valida prerequisitos (dependencias satisfechas, estado correcto, agente definido)
   - Delega la implementación al agente asignado en la fase
   - Lanza code-reviewer sobre los cambios producidos
   - Actualiza el estado de la fase en el .md correspondiente y en plan.md
3. Reporta al usuario la fase completada, archivos modificados y próxima fase disponible
