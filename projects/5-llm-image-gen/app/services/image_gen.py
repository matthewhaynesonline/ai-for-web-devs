import os

import torch
from diffusers import (
    FluxPipeline,
    StableDiffusionPipeline,
    DPMSolverMultistepScheduler,
    LCMScheduler,
    AutoPipelineForText2Image,
)

from services.fs_utils import get_safe_file_name


class ImageGen:
    def __init__(self, images_dir: str):
        self.images_dir = images_dir
        self.torch_dtype = torch.float16
        self.pipeline_variant = "fp16"
        self.bypass_safety_checker = True

        if torch.cuda.is_bf16_supported():
            self.torch_dtype = self.torch_dtype

        # https://huggingface.co/blog/lcm_lora
        self.model_id = "Lykon/absolute-reality-1.0"
        self.adapter_id = "latent-consistency/lcm-lora-sdv1-5"
        self.pipeline = self.get_sd_15_lcm_pipeline(
            model_id=self.model_id, adapter_id=self.adapter_id
        )

        # self.model_id = "stabilityai/stable-diffusion-2-1"
        # self.pipeline = self.get_sd_21_pipeline(
        #     model_id=self.model_id
        # )

        # self.model_id = "black-forest-labs/FLUX.1-schnell"
        # self.pipeline = self.get_flux_1_pipeline(
        #     model_id=self.model_id
        # )

    def get_sd_15_lcm_pipeline(
        self, model_id: str, adapter_id: str
    ) -> AutoPipelineForText2Image:
        # https://huggingface.co/latent-consistency/lcm-lora-sdv1-5

        if self.bypass_safety_checker:
            pipeline = AutoPipelineForText2Image.from_pretrained(
                model_id,
                torch_dtype=self.torch_dtype,
                variant=self.pipeline_variant,
                safety_checker=None,
            )
        else:
            pipeline = AutoPipelineForText2Image.from_pretrained(
                model_id,
                torch_dtype=self.torch_dtype,
                variant=self.pipeline_variant,
            )

        pipeline.scheduler = LCMScheduler.from_config(pipeline.scheduler.config)
        pipeline.to("cuda")

        # load and fuse lcm lora
        pipeline.load_lora_weights(adapter_id)
        pipeline.fuse_lora()

        return pipeline

    def get_sd_21_pipeline(self, model_id: str) -> StableDiffusionPipeline:
        if self.bypass_safety_checker:
            pipeline = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=self.torch_dtype,
                variant=self.pipeline_variant,
                safety_checker=None,
            )
        else:
            pipeline = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=self.torch_dtype,
                variant=self.pipeline_variant,
            )

        pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
            pipeline.scheduler.config
        )
        pipeline = pipeline.to("cuda")

        return pipeline

    def get_flux_1_pipeline(self, model_id: str) -> FluxPipeline:
        if self.bypass_safety_checker:
            pipeline = FluxPipeline.from_pretrained(
                model_id,
                torch_dtype=self.torch_dtype,
                variant=self.pipeline_variant,
                safety_checker=None,
            )
        else:
            pipeline = FluxPipeline.from_pretrained(
                model_id,
                torch_dtype=self.torch_dtype,
                variant=self.pipeline_variant,
            )

        pipeline = pipeline.to("cuda")
        # pipeline.enable_model_cpu_offload()

        return pipeline

    def gen_image_from_prompt(self, prompt: str) -> str:
        # height = 512
        # width = 512
        guidance_scale = 0.0
        num_inference_steps = 4
        # max_sequence_length = 256
        # generator = torch.Generator(device="cuda").manual_seed(30)
        # negative_prompt = "poor details"

        filename = get_safe_file_name(prompt, file_extension=".png")
        image_filepath = self.get_image_filepath(filename)

        # image = self.pipeline(prompt).images[0]

        image = self.pipeline(
            prompt=prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
        ).images[0]

        # image = self.pipeline(
        #     prompt, height=height, width=width, guidance_scale=0.0, num_inference_steps=4, max_sequence_length=256
        # ).images[0]

        image.save(image_filepath)

        return filename

    def get_image_filepath(self, filename: str) -> str:
        image_filepath = os.path.join(self.images_dir, filename)

        return image_filepath
