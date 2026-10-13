"""Dados e validação reutilizáveis para pedidos de separação."""


class Order:
    def __init__(self, order_id, items):
        self.order_id = order_id
        self.items = [dict(item, separated=0) for item in items]

    @staticmethod
    def _matches(item, box):
        product = box.product
        return (
            item["category"] == box.destination
            and item["reference"] == product["reference"]
            and (item.get("size") in (None, "-") or item["size"] == product["size"])
        )

    def matching_item(self, box):
        return next((item for item in self.items if self._matches(item, box)), None)

    def can_separate(self, box):
        item = self.matching_item(box)
        return item is not None and item["separated"] < item.get("quantity", 1)

    def separate(self, box):
        item = self.matching_item(box)
        if item is None:
            return False, "Este produto não corresponde ao pedido."
        if item["separated"] >= item.get("quantity", 1):
            return False, "Quantidade deste item já foi atendida."
        item["separated"] += 1
        return True, "ITEM SEPARADO"

    @property
    def separated_count(self):
        return sum(item["separated"] for item in self.items)

    @property
    def total_count(self):
        return sum(item.get("quantity", 1) for item in self.items)

    @property
    def completed(self):
        return self.separated_count == self.total_count
