from app.rag.pinecone import PineconeService


def main() -> None:
    service = PineconeService()

    stats = service.describe_index_stats()

    print(stats)


if __name__ == "__main__":
    main()