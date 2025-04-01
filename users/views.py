from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from users.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer


class ManageUserView(generics.RetrieveUpdateAPIView):
    """
    API view to manage authenticated user details.

    This view allows authenticated users
    to retrieve and update their own user details.

    Methods:
        get_object(): Returns the authenticated user object.
    """

    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
