from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import *

class CreateForm(forms.Form):
    item_name = forms.CharField(label="Item Name (REQUIRED)",
    widget=forms.TextInput
    (attrs={'placeholder':'Type Item Name Here', 'class':'card cardbox', 'style':'width: 18rem;'})
    )
    category = forms.CharField(label="Category", required=False,
    widget=forms.TextInput
    (attrs={'placeholder':'Type Category Here', 'class':'card cardbox', 'style':'width: 18rem;'})
    )
    item_detail = forms.CharField(label="Item Detail", required=False,
    widget=forms.TextInput
    (attrs={'placeholder':'Type Item Detail Here', 'class':'card cardbox', 'style':'width: 18rem;'})
    )
    image = forms.URLField(label="Image URL", required=False,
    widget=forms.TextInput
    (attrs={'placeholder':'Type Image Url Here', 'class':'card cardbox', 'style':'width: 18rem;'})
    )
    price = forms.DecimalField(label="Item Price (REQUIRED)", decimal_places=2,
    widget=forms.NumberInput
    (attrs={'placeholder':'Type Item Price Here', 'class':'card cardbox', 'style':'width: 18rem;'})
    )

class BidForm(forms.Form):
    bid = forms.DecimalField(label="Bid", decimal_places=2,
    widget=forms.NumberInput
    (attrs={'placeholder':'Type Bid Here', 'class':'card cardbox', 'style':'width: 18rem;'})
    )

def index(request):

    # Display watchers if signed in
    try:
        watchers = Watchlist.objects.filter(people=request.user)
    except:
        watchers = 0

    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(sold=False),
        "watchers": watchers,
    })


def login_view(request):

    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            messages.info(request, "Logged In!")
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Logged Out!")
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        messages.info(request, "Registered!")
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

def listing(request, listing):

    # Display watchers if signed in
    try:
        watchers = Watchlist.objects.filter(people=request.user)
    except:
        watchers = 0

    listing = Listing.objects.get(item_name=listing)
    bids = Bid.objects.filter(listing=listing).order_by('bid_price').all()
    comments = Comment.objects.filter(listing=listing).order_by('date').all()
    bid = bids.last()
    sold_status = listing.sold
    try:
        user = User.objects.get(username=request.user.username)
        own_listing = listing.lister.username == user.username      
    except:
        own_listing = False

    # Check current bidder for item
    try: 
        bidder = bid.values("bidder")[0]["bidder"] == request.user.id
    except: 
        bidder = False

    # If user clicked on watchlist
    if "watchlist" in request.GET:

        if not request.user.is_authenticated:
            messages.info(request, "Please log in to access watchlist!")
            return HttpResponseRedirect(reverse("listing", args=(listing.item_name,)))

        if own_listing:
            messages.info(request, "Cannot watchlist your own listing!")
            return HttpResponseRedirect(reverse("listing", args=(listing.item_name,)))

        if Watchlist.objects.filter(listing=listing).exists():
            Watchlist.objects.get(listing=listing).delete()
            messages.info(request, "Watchlist Removed!")

        else:
            add_watchlist = Watchlist(listing=listing, people=user)
            add_watchlist.save()
            messages.info(request, "Watchlist Added!")

        return HttpResponseRedirect(reverse("listing", args=(listing.item_name,)))

    # If user commented
    if "comment" in request.GET:

        if not request.user.is_authenticated:
            messages.info(request, "Please log in to comment!")
            return HttpResponseRedirect(reverse("listing", args=(listing.item_name,)))

        comment = request.GET["comment"]
        add_comment = Comment(listing=listing, comments=comment, person=user)
        add_comment.save()
        messages.info(request, "Comment Posted!")

        return HttpResponseRedirect(reverse("listing", args=(listing.item_name,)))

    # Check post request
    if request.method == "POST": 

        # If lister presses delete
        if own_listing and "delete" in request.POST:
            listing.delete()
            messages.info(request, "Your listing has been deleted!")
            return HttpResponseRedirect(reverse("index"))

        # For closing listing
        if own_listing and "close" in request.POST:
            listing.sold = True
            listing.save()
            return HttpResponseRedirect(reverse("listing", args=(listing.item_name,)))

        # If not logged in
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to bid!")
            return HttpResponseRedirect(reverse("listing", args=(listing.item_name,)))

        new_bid_price = request.POST["bid"]

        # If user was the lister
        if own_listing:
            messages.info(request, "You cannot bid on your own auction!")
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "bid": bid,
                "bidder": bidder,
                "bid_count": len(bids),
                "comments": comments,
                "own_listing": own_listing,
                "watchers": watchers,
                "sold_status": sold_status,
                "form": BidForm()
            })         
    
        # If not first bid
        try:
            # If user is already the highest bidder
            if bid.bidder == user:
                messages.info(request, "Your bid is already the highest!")
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "bid": bid,
                    "bidder": bidder,
                    "bid_count": len(bids),
                    "comments": comments,
                    "own_listing": own_listing,
                    "watchers": watchers,
                    "sold_status": sold_status,
                    "form": BidForm()
                })

            # Check if bid is higher than last
            if bid.bid_price >= float(new_bid_price):
                messages.info(request, "Bid needs to exceed current price!")
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "bid": bid,
                    "bidder": bidder,
                    "bid_count": len(bids),
                    "comments": comments,
                    "own_listing": own_listing,
                    "watchers": watchers,
                    "sold_status": sold_status,
                    "form": BidForm()
                })

            new_bid = Bid(listing=listing, bidder=user, bid_price=new_bid_price)
            new_bid.save()

            messages.info(request, "Bid has been placed!")
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "bid": new_bid,
                "bidder": new_bid,
                "bid_count": len(bids),
                "comments": comments,
                "own_listing": own_listing,
                "watchers": watchers,
                "sold_status": sold_status,
                "form": BidForm()
            })

        # For first bid
        except:

            # Check if bid is higher than initial price
            if listing.price >= float(new_bid_price):
                messages.info(request, "Bid needs to exceed current price!")
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "bid": bid,
                    "bidder": bidder,
                    "bid_count": len(bids),
                    "comments": comments,
                    "own_listing": own_listing,
                    "watchers": watchers,
                    "sold_status": sold_status,
                    "form": BidForm()
                })
            
            new_bid = Bid(listing=listing, bidder=user, bid_price=new_bid_price)
            new_bid.save()

            messages.info(request, "Bid has been placed!")
            return render(request, "auctions/listing.html", {
                "listing": listing,
                "bid": new_bid,
                "bidder": new_bid,
                "bid_count": len(bids),
                "comments": comments,
                "own_listing": own_listing,
                "watchers": watchers,
                "sold_status": sold_status,
                "form": BidForm()
            })

    return render(request, "auctions/listing.html", {
        "listing": listing,
        "bid": bid,
        "bidder": bidder,
        "bid_count": len(bids),
        "comments": comments,
        "own_listing": own_listing,
        "watchers": watchers,
        "sold_status": sold_status,
        "form": BidForm()
    })

def create_listing(request):

    # In case GET request is manually typed
    if not request.user.is_authenticated:
        messages.info(request, "Please log in create a listing!")
        return HttpResponseRedirect(reverse("login"))

    if request.method == "POST":

        category = request.POST["category"]
        item_name = request.POST["item_name"]
        item_detail = request.POST["item_detail"]
        image = request.POST["image"]
        price = request.POST["price"]
        lister = User.objects.get(username=request.user.username)

        # # Check if image URL is viable
        # image_valid = False
        # for type in [".png", ".jpg", ".jpeg"]:
        #     if type in image:
        #         image_valid = True
        # if not image_valid and image:
        #     messages.info(request, "Image URL invalid!")
        #     return HttpResponseRedirect(reverse("index"))
        if image == "":
            image = "files/listings/No-Image-Placeholder.svg.png"

        # Create new list in Listing Database
        new_list = Listing(category=category, item_name=item_name, item_detail=item_detail, image=image, price=price, lister=lister)
        new_list.save()

        messages.info(request, "Listing Success!")
        return HttpResponseRedirect(reverse("index"))


    return render(request, "auctions/create.html", {
        "watchers": Watchlist.objects.filter(people=request.user),
        "form": CreateForm()
    })

def watch(request):

    # In case GET request is manually typed
    if not request.user.is_authenticated:
        messages.info(request, "Please log in view watchlist!")
        return HttpResponseRedirect(reverse("login"))

    return render(request, "auctions/watchlist.html", {
        "watchlists": Watchlist.objects.filter(people=request.user).all(),
        "watchers": Watchlist.objects.filter(people=request.user),
    })

def category(request):

    # In case GET request is manually typed
    if not request.user.is_authenticated:
        messages.info(request, "Please log in view categories!")
        return HttpResponseRedirect(reverse("login"))

    return render(request, "auctions/category.html", {
        "categories": Listing.objects.exclude(category="").exclude(sold=True).distinct().values("category"),
        "watchers": Watchlist.objects.filter(people=request.user),
    })

@login_required
def category_list(request, category_list):

    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(category=category_list, sold=False),
        "watchers": Watchlist.objects.filter(people=request.user),
    })