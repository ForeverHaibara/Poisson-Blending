# Poisson-Blending
A python implementation of Poisson Blending with friendly user interface.

## Dependencies 
1. **numpy**
2. **scipy**
3. **PIL**
4. **tkinter** == 8.6
5. **numba** (optional but recommended)

If **numba** is installed, the program will be twice faster. Don't be afraid, it won't be long -- the problem gets solved within seconds. 

## Quick Start

Just run **main.py** and follow the instructions! You will obtain the result within $5$ steps! (Upload the foreground, crop out the target, upload the background, place the target onto the background and finally save the result.)

We have also prepared some images for testing in the **examples** folder. They are collected from the original paper and from the Internet. Please issue me to remove them  in the case of copyright infringement.

## Example

Original artwork created by lofter 小若.
<!---
![image](https://raw.githubusercontent.com/ForeverHaibara/Poisson-Blending/main/2022年6月9日8.png)
-->

![image](https://github.com/ForeverHaibara/Poisson-Blending/blob/main/examples/display.png?raw=true)


## Reference

1. [J. Martino, Gabriele Facciolo, and Enric Meinhardt-Llopis.  Poisson image editing.Image Processing On Line,5:300–325, 11 2016.6.](https://dl.acm.org/doi/10.1145/882262.882269)
