from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class User(AbstractUser):
    currency = models.FloatField(default=1000.00)

    def __str__(self):
        return f"{self.id}: {self.username}"

class Listing(models.Model):
    category = models.CharField(max_length=64, blank=True)
    item_name = models.CharField(max_length=64)
    item_detail = models.CharField(max_length=64, blank=True)
    image = models.ImageField(upload_to="files/listings", blank=True)
    price = models.FloatField(validators=[MinValueValidator(0.01)])
    date = models.DateTimeField(auto_now_add=True)
    lister = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    sold = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.item_name}: ${'{:.2f}'.format(float(self.price))} - listed by {self.lister.username} at {self.date}"

class Bid(models.Model):

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids_list")
    bid_price = models.FloatField()

    def __str__(self):
        return f"{self.listing}: ${'{:.2f}'.format(float(self.bid_price))} - {self.bidder}"

class Comment(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    comments = models.TextField()
    person = models.ForeignKey(User, on_delete=models.CASCADE, related_name="commenter")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.listing}: {self.comments} @ {self.date}"

class Watchlist(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="watchlists")
    people = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchers")

    def __str__(self):
        return f"{self.listing}: {self.people}"