from rest_framework.routers import DefaultRouter

from .views import TicketViewSet, TicketMessageViewSet


router = DefaultRouter()

router.register("tickets", TicketViewSet, basename="ticket")
router.register("messages", TicketMessageViewSet, basename="message")

urlpatterns = router.urls