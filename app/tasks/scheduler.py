from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import date
from app.messaging.producer_relatorio import solicitar_relatorio_frequencia
import asyncio


def agendar_envio_relatorio():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        lambda: solicitar_relatorio_frequencia(date.today()),
        trigger='cron', hour=23, minute=59
    )
    scheduler.start()


if __name__ == "__main__":
    agendar_envio_relatorio()
    asyncio.get_event_loop().run_forever()
