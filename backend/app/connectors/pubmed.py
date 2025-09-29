import requests
import xml.etree.ElementTree as ET

def search_pubmed(query: str, max_results: int = 10):
    """
    Searches PubMed for articles matching the query and returns a list of titles and abstracts.
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    search_url = f"{base_url}esearch.fcgi"
    fetch_url = f"{base_url}efetch.fcgi"

    # Search for article IDs
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
    }
    try:
        response = requests.get(search_url, params=search_params)
        response.raise_for_status()
        search_results = response.json()
        id_list = search_results.get("esearchresult", {}).get("idlist", [])

        if not id_list:
            return []

        # Fetch article details
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml",
        }
        response = requests.get(fetch_url, params=fetch_params)
        response.raise_for_status()

        # Parse XML response
        root = ET.fromstring(response.content)
        articles = []
        for article in root.findall(".//PubmedArticle"):
            title_element = article.find(".//ArticleTitle")
            abstract_element = article.find(".//AbstractText")
            title = title_element.text if title_element is not None else "No title available"
            abstract = abstract_element.text if abstract_element is not None else "No abstract available"
            articles.append({"title": title, "abstract": abstract})

        return articles

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during PubMed API request: {e}")
        return []
    except ET.ParseError as e:
        print(f"An error occurred parsing XML from PubMed: {e}")
        return []