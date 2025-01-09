#!/usr/bin/env python
# coding: utf-8

# In this project we will build a nice web app that allows you to swap out the background of a subject and substitute it with an image generated by Stable Diffusion through a text prompt:
# 
# ![image.png](attachment:image.png)
# 
# Let's start by importing what we need:

# In[1]:


from PIL import Image
import requests
from transformers import SamModel, SamProcessor
from diffusers import DiffusionPipeline, AutoPipelineForText2Image, AutoPipelineForInpainting
from diffusers.utils import load_image, make_image_grid
import huggingface_hub

import torch
import numpy as np


# ## SAM
# 
# Complete the following cell by loading the pretrained SAM from Facebook/Meta. Remember to:
# 
# 1. Move the model to the GPU by adding `.to("cuda")`
# 2. Add the option `torch_dtype=torch.float16` to your call of AutoPipelineForInpainting.from_pretrained
# 
# This cell might take a couple of minutes to load.

# In[2]:


# Load the SAM model as we have seen in the class
# Remeber to load it on the GPU by adding .to("cuda")
# at the end
model = SamModel.from_pretrained("facebook/sam-vit-base").to("cuda")

# Load the SamProcessor using the facebook/sam-vit-base
# checkpoint
processor = SamProcessor.from_pretrained("facebook/sam-vit-base")


# ### Get the mask
# 
# Now that you have loaded SAM, complete the following function that uses SAM to produce a segmentation mask:

# In[3]:


def mask_to_rgb(mask):
    """
    Transforms a binary mask into an RGBA image for visualization
    """
    
    bg_transparent = np.zeros(mask.shape + (4, ), dtype=np.uint8)
    
    # Color the area we will replace in green
    # (this vector is [Red, Green, Blue, Alpha])
    bg_transparent[mask == 1] = [0, 255, 0, 127]
    
    return bg_transparent


def get_processed_inputs(image, input_points):
    
    # Use the processor to generate the right inputs
    # for SAM
    # Use "image" as your image
    # Use 'input_points' as your input_points,
    # and remember to use the option return_tensors='pt'
    # Also, remember to add .to("cuda") at the end
    inputs = processor(image, input_points, return_tensors="pt").to("cuda")
    
    # Call SAM
    outputs = model(**inputs)
    
    # Now let's post process the outputs of SAM to obtain the masks
    masks = processor.image_processor.post_process_masks(
       outputs.pred_masks.cpu(), 
       inputs["original_sizes"].cpu(), 
       inputs["reshaped_input_sizes"].cpu()
    )
    
    # Here we select the mask with the highest score
    # as the mask we will use. You can experiment with also
    # other selection criteria, for example the largest mask
    # instead of the most confident mask
    best_mask = masks[0][0][outputs.iou_scores.argmax()] 

    # NOTE: we invert the mask by using the ~ operator because
    # so that the subject pixels will have a value of 0 and the
    # background pixels a value of 1. This will make it more convenient
    # to infill the background
    return ~best_mask.cpu().numpy()


# Now let's test what we have done so far. By executing this cell you should get a visualization of the mask for the following car:
# 
# <img src='car.png' width="200px"></img>
# 
# Let's see what happens in this cell:
# 1. We open the image of the car and **we resize it to 512 by 512 pixels** (a square image). This makes things simpler for this project
# 2. We define a few points on the image that indicate where the car is
# 3. We use the function we have defined to generate a mask using SAM
# 4. We visualize the mask
# 
# The mask should look like this:
# 
# ![image-2.png](attachment:image-2.png)
# 
# If it doesn't or you get errors, double check the code you have completed above and fix it before moving on.

# In[4]:


raw_image = Image.open("car.png").convert("RGB").resize((512, 512))

# These are the coordinates of two points on the car
input_points = [[[150, 170], [300, 250]]]

mask = get_processed_inputs(raw_image, input_points)

Image.fromarray(mask_to_rgb(mask)).resize((128, 128))


# ## Inpainting
# 
# Now that we have completed the SAM setup, let's move to the inpainting setup.
# 
# Let's start by loading our inpainting pipeline. We will use the `diffusers/stable-diffusion-xl-1.0-inpainting-0.1` pretrained model and the `AutoPipelineForInpainting` as we have seen in our `diffusers` demo in Lesson 5.
# 
# Complete the following code and run it (it might take a few minutes to run):
# 
# > **NOTE**: you will probably see a warning similar to ``The config attributes {'decay'...``. Please ignore it. It is a warning generated by the diffusers library that does not constitute a problem for our application

# In[5]:


# Load the AutoPipelineForInpainting pipeline 
# (remember the diffusers demo in lesson 5)
# The checkpoint we want to use is 
# "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"
# Remember to add torch_dtype=torch.float16 as an option

pipeline = AutoPipelineForInpainting.from_pretrained("diffusers/stable-diffusion-xl-1.0-inpainting-0.1",torch_dtype=torch.float16)

# This will make it more efficient on our hardware
pipeline.enable_model_cpu_offload()


# Now complete the following function that gets in input:
# 1. The raw image
# 2. The mask generated by SAM (a numpy array)
# 3. The text prompt for the infill
# 4. An optional negative prompt
# 5. An optional seed for repeatibility
# 6. The Classifier-Free Guidance Scale (CFGS). If you don't remember what this is, refer to the Text Conditioning explanation in Lesson 5

# In[6]:


def inpaint(raw_image, input_mask, prompt, negative_prompt=None, seed=74294536, cfgs=7):
    
    mask_image = Image.fromarray(input_mask)
    
    rand_gen = torch.manual_seed(seed)
    
    # Use the pipeline we have created in the previous cell
    # Use "prompt" as prompt, 
    # "negative_prompt" as the negative prompt,
    # raw_image as the image,
    # mask_image as the mask_image,
    # rand_gen as the generator and
    # cfgs as the guidance_scale
    
    image = pipeline(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=raw_image,
        mask_image=mask_image,
        generator=rand_gen,
        guidance_scale=cfgs
    ).images[0]
    
    return image


# Let's test our inpainting on the mask we have obtained earlier with SAM:

# In[7]:


prompt = "a car driving on Mars. Studio lights, 1970s"
negative_prompt = "artifacts, low quality, distortion"

image = inpaint(raw_image, mask, prompt, negative_prompt)


# Let's have a look at what we have produced:

# In[8]:


fig = make_image_grid([raw_image, Image.fromarray(mask_to_rgb(mask)), image.resize((512, 512))], rows=1, cols=3)
fig


# ## Interactive app
# 
# To make things a bit more fun, we have prepared an interactive app for you that uses the code you have completed and allow you to upload an image, run SAM, and generate the new background through a text prompt.
# 
# Simply execute the following cell. The output will contain a preview of the app: **DO NOT USE IT**. Instead, you will also see a link similar to this:
# 
# ![image.png](attachment:image.png)
# 
# Click on the second link (the public URL), from there you will be able to use the app much more comfortably.
# 
# > NOTE: if for any reason you need to stop the app, click on the stop icon of the jupyter interface: ![image-3.png](attachment:image-3.png)  then **execute the next cell containing the code `my_app.close`**
# 

# In[9]:


import app


# In[ ]:


my_app = app.generate_app(get_processed_inputs, inpaint)


# In[ ]:


my_app.close()


# In[ ]:




