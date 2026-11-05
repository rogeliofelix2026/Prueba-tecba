from pydantic_settings import BaseSettings, SettingsConfigDict
import psycopg


class Settings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def main() -> None:
    settings = Settings()

    with psycopg.connect(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)

            tables = cursor.fetchall()

    print("✅ Conexión exitosa con Supabase")
    print()
    print("Tablas del esquema public:")

    for (table_name,) in tables:
        print(f"  - {table_name}")


if __name__ == "__main__":
    main()