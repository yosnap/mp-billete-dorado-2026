"""
Celery Beat schedule para emails de campaña programados.

Fechas clave de la campaña MP Billete Dorado 2026:
  - Inicio:      15-jun-2026
  - Last chance: 23-sep-2026  (7 días antes del cierre)
  - Grand final: 30-sep-2026  (cierre de campaña)

Se importa en celery_app.py y se fusiona con celery_app.conf.beat_schedule.
"""
from celery.schedules import crontab

# Clave → definición de tarea programada para Celery Beat
NOTIFICATIONS_BEAT_SCHEDULE: dict = {
    # Última oportunidad — 23-sep-2026 a las 09:00 (America/Bogota)
    "last-chance-email-2026-09-23": {
        "task": "notifications.send_bulk_campaign",
        "schedule": crontab(hour=9, minute=0, day_of_month=23, month_of_year=9),
        "args": [],
        "kwargs": {
            "email_type": "last_chance",
            "context": {
                "campaign_name": "MP Billete Dorado 2026",
                "deadline_date": "30 de septiembre de 2026",
                "campaign_url": "https://billетедоrado.mainpaper.com",
            },
        },
        # one_off=True equivalente: se configura en el scheduler externo si se usa
        # django-celery-beat; aquí se documenta la intención de ejecución única.
        "options": {"expires": 86400},  # expira si no se procesa en 24h
    },
    # Gran final — 30-sep-2026 a las 09:00 (America/Bogota)
    "grand-final-email-2026-09-30": {
        "task": "notifications.send_bulk_campaign",
        "schedule": crontab(hour=9, minute=0, day_of_month=30, month_of_year=9),
        "args": [],
        "kwargs": {
            "email_type": "grand_final",
            "context": {
                "campaign_name": "MP Billete Dorado 2026",
                "final_date": "30 de septiembre de 2026",
                "campaign_url": "https://billetedorado.mainpaper.com",
            },
        },
        "options": {"expires": 86400},
    },
}
