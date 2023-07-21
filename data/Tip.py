class Tip:
    def __init__(self, author, content, rating=0):
        self.author = author
        self.content = content
        self.rating = rating

    def create_tip_message(self):
        # *(+/-rating)* **Tip from author**:\ncontent
        return "*({0:+})* **Tip from {1}**:\n{2}".format(self.rating, self.author, self.content)

    def __repr__(self):
        return f"({self.rating}) {self.author}"
