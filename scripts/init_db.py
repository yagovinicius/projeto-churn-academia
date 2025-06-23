from app.models.models import Base, db


def init_db():
    Base.metadata.create_all(db)
    print('Tabelas criadas com sucesso!')


if __name__ == '__main__':
    init_db()
