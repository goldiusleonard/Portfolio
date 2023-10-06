$(document).ready(() => {
    setInterval(() => {
        let containerWidth = $("#slider-container").width()
        let left = $("#image-roll").css("left").split("px")[0]
        let imageCount = 3

        if(left == containerWidth * -1 * (imageCount - 1)){
            $("#image-roll").animate({left: 0})
        }
        else{
            $("#image-roll").animate({left: left - containerWidth})
        }
        
    }, 2000)
})