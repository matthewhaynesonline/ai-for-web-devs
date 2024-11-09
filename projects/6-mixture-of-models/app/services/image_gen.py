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

        self.pipe_variant = "fp16"
        self.bypass_safety_checker = True
        self.use_torch_compile = False

        if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
            self.torch_dtype = torch.bfloat16

        # https://huggingface.co/docs/diffusers/tutorials/fast_diffusion#torchcompile
        if self.use_torch_compile:
            torch._inductor.config.conv_1x1_as_mm = True
            torch._inductor.config.coordinate_descent_tuning = True
            torch._inductor.config.epilogue_fusion = False
            torch._inductor.config.coordinate_descent_check_all_directions = True

        # https://huggingface.co/blog/lcm_lora
        self.model_id = "Lykon/absolute-reality-1.0"
        self.adapter_id = "latent-consistency/lcm-lora-sdv1-5"
        self.pipe = self.get_sd_15_lcm_pipeline(
            model_id=self.model_id, adapter_id=self.adapter_id
        )

        # self.model_id = "black-forest-labs/FLUX.1-schnell"
        # self.pipe = self.get_flux_1_pipeline(model_id=self.model_id)

        if self.use_torch_compile:
            self.pipe.unet.to(memory_format=torch.channels_last)
            self.pipe.vae.to(memory_format=torch.channels_last)

            self.pipe.unet = torch.compile(
                self.pipe.unet, mode="max-autotune", fullgraph=True
            )
            self.pipe.vae.decode = torch.compile(
                self.pipe.vae.decode, mode="max-autotune", fullgraph=True
            )

    def get_sd_15_lcm_pipeline(
        self, model_id: str, adapter_id: str
    ) -> AutoPipelineForText2Image:
        # https://huggingface.co/latent-consistency/lcm-lora-sdv1-5

        if self.bypass_safety_checker:
            pipe = AutoPipelineForText2Image.from_pretrained(
                model_id,
                torch_dtype=self.torch_dtype,
                variant=self.pipe_variant,
                safety_checker=None,
            )
        else:
            pipe = AutoPipelineForText2Image.from_pretrained(
                model_id,
                torch_dtype=self.torch_dtype,
                variant=self.pipe_variant,
            )

        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)

        if torch.cuda.is_available():
            pipe = pipe.to("cuda")

        # load and fuse lcm lora
        pipe.load_lora_weights(adapter_id)
        pipe.fuse_lora()

        return pipe

    def get_flux_1_pipeline(self, model_id: str) -> FluxPipeline:
        pipe = FluxPipeline.from_pretrained(
            model_id,
            torch_dtype=self.torch_dtype,
        )

        if torch.cuda.is_available():
            pipe = pipe.to("cuda")

        # pipe.enable_model_cpu_offload()

        return pipe

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

        image = self.pipe(
            prompt=prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
        ).images[0]

        # image = self.pipe(
        #     prompt, height=height, width=width, guidance_scale=0.0, num_inference_steps=4, max_sequence_length=256
        # ).images[0]

        image.save(image_filepath)

        return filename

    def get_image_filepath(self, filename: str) -> str:
        image_filepath = os.path.join(self.images_dir, filename)

        return image_filepath
