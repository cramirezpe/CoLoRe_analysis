import numpy as np 
import matplotlib.pyplot as plt

class ClsPlotter():
    @staticmethod
    def plot(cls, ax=None, **kwargs):
        if not ax: fig, ax = plt.subplots()
        