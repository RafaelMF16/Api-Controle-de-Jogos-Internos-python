from functools import cached_property

from google.cloud import firestore
from google.cloud.firestore_v1 import Client, CollectionReference


class FirestoreDatabase:
    def __init__(
        self,
        project_id: str | None,
        equipes_collection: str,
        confrontos_collection: str,
    ) -> None:
        self.project_id = project_id
        self.equipes_collection_name = equipes_collection
        self.confrontos_collection_name = confrontos_collection

    @cached_property
    def client(self) -> Client:
        if self.project_id:
            return firestore.Client(project=self.project_id)
        return firestore.Client()

    @property
    def equipes_collection(self) -> CollectionReference:
        return self.client.collection(self.equipes_collection_name)

    @property
    def confrontos_collection(self) -> CollectionReference:
        return self.client.collection(self.confrontos_collection_name)
