import cv2
import numpy as np
import umap
import matplotlib
import pandas as pd
import plotly.graph_objects as go  # Use graph_objects for more control
import base64

from hdbscan import HDBSCAN
from Katna import config
from skimage.filters.rank import entropy
from skimage.morphology import disk
from scipy.ndimage import gaussian_filter1d
from multiprocessing import Pool
from scipy.spatial.distance import pdist, squareform

matplotlib.use("Agg")


class ImageSelector(object):
    """Class for selection of best top N images from input list of images, Currently following selection method are implemented:
    brightness filtering, contrast/entropy filtering, clustering of frames and variance of laplacian for non blurred images
    selection

    :param object: base class inheritance
    :type object: class:`Object`
    """

    def __init__(self, n_processes=1):
        # Setting number of processes for Multiprocessing Pool Object
        self.n_processes = n_processes

        # Setting for optimum Brightness values
        self.min_brightness_value = config.ImageSelector.min_brightness_value
        self.max_brightness_value = config.ImageSelector.max_brightness_value
        self.brightness_step = config.ImageSelector.brightness_step

        # Setting for optimum Contrast/Entropy values
        self.min_entropy_value = config.ImageSelector.min_entropy_value
        self.max_entropy_value = config.ImageSelector.max_entropy_value
        self.entropy_step = config.ImageSelector.entropy_step

    def __get_brightness_score__(self, image):
        """Internal function to compute the brightness of input image , returns brightness score between 0 to 100.0 ,

        :param object: base class inheritance
        :type object: class:`Object`
        :param image: input image
        :type image: Opencv Numpy Image
        :return: result of Brightness measurment
        :rtype: float value between 0.0 to 100.0
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        _, _, v = cv2.split(hsv)
        sum = np.sum(v, dtype=np.float32)
        num_of_pixels = v.shape[0] * v.shape[1]
        brightness_score = (sum * 100.0) / (num_of_pixels * 255.0)
        return brightness_score

    def __get_entropy_score__(self, image):
        """Internal function to compute the entropy/contrast of input image , returns entropy score between 0 to 10 ,

        :param object: base class inheritance
        :type object: class:`Object`
        :param image: input image
        :type image: Opencv Numpy Image
        :return: result of Entropy measurment
        :rtype: float value between 0.0 to 10.0
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        entr_img = entropy(gray, disk(5))
        all_sum = np.sum(entr_img)
        num_of_pixels = entr_img.shape[0] * entr_img.shape[1]
        entropy_score = (all_sum) / (num_of_pixels)

        return entropy_score

    def __variance_of_laplacian__(self, image):
        """Internal function to compute the laplacian of the image and then return the focus
        measure, which is simply the variance of the laplacian,

        :param object: base class inheritance
        :type object: class:`Object`
        :param image: input image
        :type image: Opencv Numpy Image
        :return: result of cv2.Laplacian
        :rtype: opencv image of type CV_64F
        """

        return cv2.Laplacian(image, cv2.CV_64F).var()

    def __filter_optimum_brightness_and_contrast_images__(self, input_img_files):
        """Internal function for selection of given input images with following parameters :optimum brightness and contrast range ,
        returns array of image files which are in optimum brigtness and contrast/entropy range.

        :param object: base class inheritance
        :type object: class:`Object`
        :param files: list of input image files
        :type files: python list of images
        :return: Returns list of filtered images
        :rtype: python list of images
        """

        n_files = len(input_img_files)

        # -------- calculating the brightness and entropy score by multiprocessing ------
        pool_obj = Pool(processes=self.n_processes)

        # self.pool_obj_entropy = Pool(processes=self.n_processes)
        with pool_obj:
            brightness_score = np.array(
                pool_obj.map(self.__get_brightness_score__, input_img_files)
            )

            entropy_score = np.array(
                pool_obj.map(self.__get_entropy_score__, input_img_files)
            )

        # -------- Check if brightness and contrast scores are in the min and max defined range ------
        brightness_ok = np.where(
            np.logical_and(
                brightness_score > self.min_brightness_value,
                brightness_score < self.max_brightness_value,
            ),
            True,
            False,
        )
        contrast_ok = np.where(
            np.logical_and(
                entropy_score > self.min_entropy_value,
                entropy_score < self.max_entropy_value,
            ),
            True,
            False,
        )

        # Returning only those images which are have good brightness and contrast score

        return [
            input_img_files[i]
            for i in range(n_files)
            if brightness_ok[i] and contrast_ok[i]
        ]

    def __save_cluster_visualization__(
        self, images, histograms, labels, output_path="interactive_clusters.html"
    ):
        """Creates an interactive UMAP visualization with image thumbnails and cluster labels as color."""

        reducer = umap.UMAP(random_state=42, metric="cosine")
        embedding = reducer.fit_transform(histograms)

        df = pd.DataFrame(embedding, columns=["UMAP1", "UMAP2"])
        df["label"] = labels  # Add the labels to the DataFrame

        fig = go.Figure()  # Use go.Figure

        for label in df["label"].unique():
            label_df = df[df["label"] == label]
            image_base64_strings = []
            for i in label_df.index:
                image = images[i]
                img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (50, 50))
                img_bytes = cv2.imencode(".jpg", img)[1].tobytes()
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                image_base64_strings.append(f"data:image/jpeg;base64,{img_base64}")

            label_df["image"] = image_base64_strings

            fig.add_trace(
                go.Scatter(
                    x=label_df["UMAP1"],
                    y=label_df["UMAP2"],
                    mode="markers",
                    marker=dict(size=8, opacity=0.8),
                    name=str(label) if label != -1 else "Noise",
                    hovertemplate="<b>UMAP1:</b> %{x}<br><b>UMAP2:</b> %{y}<br><img src='%(image)s' width='50'><extra></extra>",
                    customdata=np.stack(
                        (label_df["image"], label_df["label"]), axis=-1
                    ),
                    hovertext=label_df["label"],
                )
            )

        fig.update_layout(
            title="Interactive HDBSCAN Clustering Visualization using UMAP",
            template="plotly_dark",
            hoverlabel=dict(bgcolor="black", font_size=12, font_family="Rockwell"),
            margin=dict(l=20, r=20, t=40, b=20),
        )

        fig.write_html(output_path)

    def __prepare_cluster_sets__(self, files):
        """Internal function for clustering input image files, returns array of indexes of each input file
        (which determines which cluster a given file belongs)

        :param object: base class inheritance
        :type object: class:`Object`
        :param files: list of input image files
        :type files: python list of opencv numpy images
        :return: Returns array containing index for each file for cluster belongingness
        :rtype: np.array
        """

        all_images = []
        all_hists = []

        # Calculating the histograms for each image and adding them into **all_hists** list
        for img_file in files:
            img = cv2.cvtColor(img_file, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([img], [0], None, [256], [0, 256])
            hist = hist.reshape((256))
            all_images.append(img)
            all_hists.append(hist)

        all_hists_normalized = np.array([hist / np.sum(hist) for hist in all_hists])

        # Optional: Apply Gaussian smoothing to the normalized histograms
        def smooth_histogram(hist, sigma=2):
            return gaussian_filter1d(hist, sigma)

        all_hists_smoothed = np.array(
            [smooth_histogram(hist) for hist in all_hists_normalized]
        )

        # Compute the pairwise cosine distance matrix
        cosine_dist_matrix = squareform(pdist(all_hists_smoothed, metric="cosine"))

        # Modify the distance transformation (less aggressive scaling)
        cosine_dist_matrix = np.power(cosine_dist_matrix, 0.5)

        num_frames = len(all_images)  # Total number of frames
        min_cluster_size = max(
            2, int(num_frames * 0.01)
        )  # 1% of total frames, but at least 2
        min_samples = max(
            1, int(num_frames * 0.001)
        )  # 0.1% of total frames, but at least 1

        # HDBSCAN clustering using the precomputed distance matrix
        clustering = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric="precomputed",
            cluster_selection_method="leaf",
            alpha=1.0,
            cluster_selection_epsilon=0.1,
            allow_single_cluster=True,
        ).fit(cosine_dist_matrix)

        labels = clustering.labels_

        # Save visualization of clusters
        # self.__save_cluster_visualization__(all_images, all_hists, labels, output_path="interactive_clusters.html")

        # Identifying the label for each image in the cluster and tagging them
        files_clusters_index_array = []
        unique_labels = set(labels)
        for label in unique_labels:
            if label == -1:  # Skip noise points
                continue
            index_array = np.where(labels == label)
            files_clusters_index_array.append(index_array)

        files_clusters_index_array = np.array(files_clusters_index_array, dtype=object)
        return files_clusters_index_array

    def __get_laplacian_scores(self, files, n_images):
        """Function to iteratee over each image in the cluster and calculates the laplacian/blurryness
           score and adds the score to a list

        :param files: list of input filenames
        :type files: python list of string
        :param n_images: number of images in the given cluster
        :type n_images: int
        :return: Returns list of laplacian scores for each image in the given cluster
        :rtype: python list
        """

        variance_laplacians = []
        # Iterate over all images in image list
        for image_i in n_images:
            img_file = files[n_images[image_i]]
            img = cv2.cvtColor(img_file, cv2.COLOR_BGR2GRAY)

            # Calculating the blurryness of image
            variance_laplacian = self.__variance_of_laplacian__(img)
            variance_laplacians.append(variance_laplacian)

        return variance_laplacians

    def __get_best_images_index_from_each_cluster__(
        self, files, files_clusters_index_array
    ):
        """Internal function returns index of one best image from each cluster

        :param object: base class inheritance
        :type object: class:`Object`
        :param files: list of input filenames
        :type files: python list of string
        :param files_clusters_index_array: Input is array containing index for each file for cluster belongingness
        :type: np.array
        :return: Returns list of filtered files which are best candidate from each cluster
        :rtype: python list
        """

        filtered_items = []

        # Iterating over every image in each cluster to find the best images from every cluster
        clusters = np.arange(len(files_clusters_index_array))
        for cluster_i in clusters:
            curr_row = files_clusters_index_array[cluster_i][0]
            # kp_lengths = []
            n_images = np.arange(len(curr_row))
            variance_laplacians = self.__get_laplacian_scores(files, n_images)

            # Selecting image with low burr(high laplacian) score
            selected_frame_of_current_cluster = curr_row[np.argmax(variance_laplacians)]
            filtered_items.append(selected_frame_of_current_cluster)

        return filtered_items

    def select_best_frames(self, input_key_frames):
        """[summary] Public function for Image selector class: takes list of key-frames images and number of required
        frames as input, returns list of filtered keyframes

        :param object: base class inheritance
        :type object: class:`Object`
        :param input_key_frames: list of input keyframes in list of opencv image format
        :type input_key_frames: python list opencv images
        :param number_of_frames: Required number of images
        :type: int
        :return: Returns list of filtered image files
        :rtype: python list of images
        """

        # filtered_key_frames = []
        filtered_images_list = []
        # # Repeat until number of frames
        # min_brightness_values = np.arange(
        #     config.ImageSelector.min_brightness_value, -0.01, -self.brightness_step
        # )
        # max_brightness_values = np.arange(
        #     config.ImageSelector.max_brightness_value, 100.01, self.brightness_step
        # )
        # min_entropy_values = np.arange(
        #     config.ImageSelector.min_entropy_value, -0.01, -self.entropy_step
        # )
        # max_entropy_values = np.arange(
        #     config.ImageSelector.max_entropy_value, 10.01, self.entropy_step
        # )

        # for (
        #     min_brightness_value,
        #     max_brightness_value,
        #     min_entropy_value,
        #     max_entropy_value,
        # ) in itertools.zip_longest(
        #     min_brightness_values,
        #     max_brightness_values,
        #     min_entropy_values,
        #     max_entropy_values,
        # ):
        #     if min_brightness_value is None:
        #         min_brightness_value = 0.0
        #     if max_brightness_value is None:
        #         max_brightness_value = 100.0
        #     if min_entropy_value is None:
        #         min_entropy_value = 0.0
        #     if max_entropy_value is None:
        #         max_entropy_value = 10.0
        #     self.min_brightness_value = min_brightness_value
        #     self.max_brightness_value = max_brightness_value
        #     self.min_entropy_value = min_entropy_value
        #     self.max_entropy_value = max_entropy_value
        #     filtered_key_frames = (
        #         self.__filter_optimum_brightness_and_contrast_images__(
        #             input_key_frames,
        #         )
        #     )

        # Selecting the best images from each cluster by first preparing the clusters on basis of histograms
        # and then selecting the best images from every cluster
        files_clusters_index_array = self.__prepare_cluster_sets__(input_key_frames)
        selected_images_index = self.__get_best_images_index_from_each_cluster__(
            input_key_frames, files_clusters_index_array
        )

        for index in selected_images_index:
            img = input_key_frames[index]
            filtered_images_list.append(img)

        return filtered_images_list
