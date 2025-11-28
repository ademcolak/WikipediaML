from src.navigator import WikiNavigator


def main():
    # Navigator objesi oluştur
    navigator = WikiNavigator()

    # Potato'dan başlayarak 5 adım rastgele gezin
    print("🎲 Random Walk Testi")
    print()

    path = navigator.random_walk(start="Potato", max_steps=5)

    print()
    print("📍 Gezilen yol:")
    for i, page in enumerate(path):
        if i < len(path) - 1:
            print(f"  {page} →")
        else:
            print(f"  {page} 🏁")


if __name__ == "__main__":
    main()