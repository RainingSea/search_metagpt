import sys
sys.path.append("/home/molyer/project/metagpt/MetaGPT-0.7-release/")

from software_company import generate_repo, ProjectRepo

# infos: 测试的 prompts
# infos=["create a snake game","create a 2048 game"]

# for info in infos:
#     repo: ProjectRepo = generate_repo(info)  # or ProjectRepo("<path>")
#     print(repo)

# repo: ProjectRepo = generate_repo("Design a centered music concert landing page within the entire page height. Include a rectangular image on the right with a height of 400px and a golden ratio aspect ratio sourced from Unsplash. The left side should have an area of the same size as the image, displaying the concert's theme and description, along with a button for ticket acquisition. Ensure the overall layout is centered both vertically and horizontally, making the entire webpage height equal to the page height. No need to implement backend logic, just design a static webpage. Please note that apart from the theme description, ticket acquisition button, and image, do not generate any other elements. try to use only simple javascript, do not use any typescript code")  # or ProjectRepo("<path>")
repo: ProjectRepo = generate_repo("create a snake game")  # or ProjectRepo("<path>")
print(repo)  # it will print the repo structure with files