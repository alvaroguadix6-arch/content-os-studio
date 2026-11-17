"""Aplica calidad.py a todas las escenas del anuncio.   python mejorar_todo.py origen/ arte/"""
import os
import sys

from calidad import mejorar, pipelines

ESCENAS = {
    "carretera": ("driver point of view inside a modern car, sunny mountain road through the windshield", None),
    "taller": ("interior of a modern bright car glass workshop, clean polished floor, LED lights", None),
    "sustitucion": ("two auto glass technicians in black polo shirts and gloves working on a silver car in a modern workshop",
                    "man in his thirties with short dark hair, focused expression | woman with dark hair tied back, focused expression"),
    "tintado": ("rear of a dark car with red tail lights in a modern workshop", None),
    "faro": ("close up of a modern car headlight, crystal clear and polished, studio lighting", None),
    "adas": ("modern silver sports car in a dark workshop, studio lighting", None),
    "camion": ("trucks and vans parked in front of a modern industrial workshop on a sunny day", None),
    "familia": ("close up of a smiling young couple in the front seats of a car, the man driving, sunny day",
                "man in his thirties with short brown hair, smiling | young woman with long wavy brown hair, smiling"),
}

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    pipe = pipelines()
    for name, (prompt, faces) in ESCENAS.items():
        mejorar(pipe, os.path.join(src, name + ".png"), os.path.join(dst, name + ".png"), prompt, faces)
