

import json
import numpy as np
import face_recognition

from database import CursorFromConnectionPool


class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class FaceDetector(metaclass=SingletonMeta): # make sure only one instance of the class is created
    def __update_faces(self):
        new_faces_name = []
        new_encoded_face = []
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT face_id, face_encodings FROM faces")
            for face_id, face_encodings in cursor.fetchall():
                new_faces_name.append(face_id)
                new_encoded_face.append(np.array(json.loads(face_encodings)))

        self.faces_name = new_faces_name
        self.faces_encoding = new_encoded_face

    def __init__(self):
        self.faces_name = []
        self.encoded_face = []
        self.__update_faces()
        
    def register_face(self, name: str, face_image: bytes):
        face: np.ndarray = face_recognition.load_image_file(face_image)
        face_encoding: list[np.ndarray] = face_recognition.face_encodings(face)[0] # only one face per image
        encode = json.dumps(face_encoding.tolist())

        with CursorFromConnectionPool() as cursor:
            if name in self.faces_name:
                cursor.execute("UPDATE faces SET face_encodings = %s WHERE face_id = %s", (encode, name))

            else:
                cursor.execute("INSERT INTO faces(face_id, face_encodings) VALUES(%s, %s)", (name, encode))

        self.__update_faces()
        
    def detect_face(self, image: bytes):
        face: np.ndarray = face_recognition.load_image_file(image)
        face_encoding: list[np.ndarray] = face_recognition.face_encodings(face)[0]
        
        if len(face_encoding) == 0:
            raise ValueError("No face detected in the image.")
        
        result : list[np.bool_] = face_recognition.compare_faces(self.faces_encoding, face_encoding)
        return dict(zip(self.faces_name, map(bool, result))) # convert np.bool_ to bool to make it JSON serializable
