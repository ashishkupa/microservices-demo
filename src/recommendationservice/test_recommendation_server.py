from unittest.mock import MagicMock

import demo_pb2
import recommendation_server


def _make_product(product_id):
    product = demo_pb2.Product()
    product.id = product_id
    return product


def test_list_recommendations_excludes_products_already_in_cart(monkeypatch):
    # Arrange: fake the product catalog service so this test never
    # touches the network. It "returns" 3 products: A, B, C.
    fake_catalog_response = demo_pb2.ListProductsResponse()
    fake_catalog_response.products.extend([
        _make_product("A"),
        _make_product("B"),
        _make_product("C"),
    ])
    fake_stub = MagicMock()
    fake_stub.ListProducts.return_value = fake_catalog_response

    # Inject our fake stub in place of the real (nonexistent-until-runtime) one.
    # raising=False because product_catalog_stub doesn't exist at import time --
    # it's only created inside `if __name__ == "__main__":`.
    monkeypatch.setattr(recommendation_server, "product_catalog_stub", fake_stub, raising=False)

    service = recommendation_server.RecommendationService()
    request = demo_pb2.ListRecommendationsRequest(product_ids=["A"])

    # Act
    response = service.ListRecommendations(request, context=None)

    # Assert: "A" is already in the customer's cart/view, so it must
    # never come back as a recommendation.
    assert "A" not in response.product_ids
    assert set(response.product_ids).issubset({"B", "C"})


def test_list_recommendations_returns_at_most_five(monkeypatch):
    # Arrange: 10 products available, none excluded.
    fake_catalog_response = demo_pb2.ListProductsResponse()
    fake_catalog_response.products.extend(
        [_make_product(f"P{i}") for i in range(10)]
    )
    fake_stub = MagicMock()
    fake_stub.ListProducts.return_value = fake_catalog_response
    monkeypatch.setattr(recommendation_server, "product_catalog_stub", fake_stub, raising=False)

    service = recommendation_server.RecommendationService()
    request = demo_pb2.ListRecommendationsRequest(product_ids=[])

    # Act
    response = service.ListRecommendations(request, context=None)

    # Assert: the code hardcodes max_responses = 5
    assert len(response.product_ids) == 5
