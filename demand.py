class Demand:
    """
    Class to model a demand of product
    """

    def __init__(self, product: str, total: float, origin: str, destination: str) -> None:
        """
        Constructor method
        Params:
            - product (str): name of the product
            - total (float): total demand, in ton
            - origin (str): id of origin terminal
            - destination (str): id of destination terminal
        """

        self.product = product
        self.total = total
        self.origin = origin
        self.destination = destination