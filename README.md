# Generative-AI-Photo-Editing-with-Inpainting

## Overview
This project involves building an interactive app to swap backgrounds or subjects in an image using Generative Models and the Segment Anything Model (SAM). The app allows users to select an object or subject in an image and replace either the background or the object with a computer-generated one based on a text description.

## Features
Upload an image and select the main subject using point inputs.

Use SAM to generate a segmentation mask for the selected subject.

Replace the background with a computer-generated one using a text-to-image diffusion model.

Alternatively, replace the subject while keeping the original background.

Refine the segmentation mask using additional input points for better accuracy.
## Project Workflow
### Upload an Image:
Users upload an image for processing.
### Select the Main Subject:
Input points are used to define the subject of interest.

SAM generates a segmentation mask around the selected subject.

Users can accept the mask or refine it with additional points.

### Generate the Replacement:

Users provide a text description for the desired background or subject.

Optionally, users can include negative prompts for enhanced customization.
### Process the Output:

A text-to-image diffusion model generates the new background or subject based on the text prompt.

Users can toggle between replacing the subject or the background.
### Display the Final Image:

The app displays the modified image with options to experiment with additional inputs and parameters.
## Key Technologies
Segment Anything Model (SAM): Used for generating segmentation masks.

Text-to-Image Diffusion Models: Generate backgrounds or subjects based on user-defined prompts.

Gradio: Provides the interactive user interface for the app.
