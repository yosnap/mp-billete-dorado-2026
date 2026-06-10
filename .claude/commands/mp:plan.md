Activa el skill `mp:plan` para crear una planificación detallada del proyecto.

Pasos a seguir:

1. Lee y carga el skill desde `.claude/skills/plan/SKILL.md`
2. Lee la referencia de plantilla en `.claude/skills/plan/references/phase-template.md`
3. Ejecuta el flujo completo del skill:
   - Scout automático del codebase (estructura, tech stack, docs existentes)
   - Captura el objetivo: usa `$ARGUMENTS` si se pasó un argumento, si no pregunta al usuario
   - Diseña las fases y asigna agentes por dominio
   - Genera la carpeta `plans/<timestamp>-<slug>/` con `plan.md` y los archivos `phase-XX-*.md`
4. Reporta al usuario el plan creado con las fases generadas y el próximo paso de implementación
