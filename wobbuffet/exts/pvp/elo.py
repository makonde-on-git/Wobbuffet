class Elo:

    def __init__(self, initial: int, k: int):
        self.initial = initial
        self.k = k

    def calculate_new_score(self, p1_points=None, p2_points=None):
        """Calculates new points for two players. Assuming player 1 won, no draws possible."""
        p1_points = self.initial if p2_points is None else p1_points
        p2_points = self.initial if p2_points is None else p2_points
        p1_rating = pow(10, p1_points/400)
        p2_rating = pow(10, p2_points/400)
        p1_expected = p1_rating / (p1_rating + p2_rating)
        p2_expected = p2_rating / (p1_rating + p2_rating)
        p1_new_points = p1_points + int(self.k * (1 - p1_expected))
        p2_new_points = p2_points + int(self.k * (0 - p2_expected))
        return p1_new_points, p2_new_points

    def get_initial(self):
        return self.initial
