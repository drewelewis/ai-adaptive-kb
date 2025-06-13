import uuid
def save_graph(filename,graph):
    try:
        # Generate a random filename
        import os

        # Ensure the images directory exists
        images_dir = "images"
        os.makedirs(images_dir, exist_ok=True)
        
        # Generate a random filename
        if filename=="" or filename==None:
            filename = os.path.join(images_dir, str(uuid.uuid4()) + ".png")
        else:
            filename = os.path.join(images_dir, filename)
        # Save the image as a file
        with open(filename, "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
   
    except Exception as e:
        # This requires some extra dependencies and is optional
        print(f"Error: {e}")
        pass

