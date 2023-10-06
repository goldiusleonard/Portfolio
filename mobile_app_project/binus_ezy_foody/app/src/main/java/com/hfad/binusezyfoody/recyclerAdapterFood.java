package com.hfad.binusezyfoody;

import android.content.Context;
import android.content.Intent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;

public class recyclerAdapterFood extends RecyclerView.Adapter<recyclerAdapterFood.MyViewHolder> {
    private ArrayList<Food> foodList;

    public recyclerAdapterFood(ArrayList<Food> foodList) {
        this.foodList = foodList;
    }

    public class MyViewHolder extends RecyclerView.ViewHolder {
        private TextView name;
        private TextView price;
        private ImageView img;
        private final Context context;

        public MyViewHolder (final View view) {
            super(view);
            this.name = view.findViewById(R.id.name);
            this.price = view.findViewById(R.id.price);
            this.img = view.findViewById(R.id.product_img);
            context = itemView.getContext();

            view.setOnClickListener(new View.OnClickListener() {

                @Override
                public void onClick(View v) {
                    Food food = foodList.get(getAdapterPosition());
                    Intent intent = new Intent(context, OrderActivity.class);
                    intent.putExtra("name", food.getName());
                    intent.putExtra("price", food.getPrice());
                    intent.putExtra("img", food.getImg());
                    intent.putExtra("position", getAdapterPosition());
                    intent.putExtra("type", "Food");
                    context.startActivity(intent);
                }
            });
        }

    }

    @NonNull
    @Override
    public recyclerAdapterFood.MyViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View itemView = LayoutInflater.from(parent.getContext()).inflate(R.layout.catalog_item, parent, false);
        return new MyViewHolder(itemView);
    }

    @Override
    public void onBindViewHolder(@NonNull recyclerAdapterFood.MyViewHolder holder, int position) {
        String name = foodList.get(position).getName();
        String price = foodList.get(position).getPrice().toString();
        int img = foodList.get(position).getImg();

        holder.name.setText(name);
        holder.price.setText(price);
        holder.img.setImageResource(img);
    }

    @Override
    public int getItemCount() {
        return foodList.size();
    }
}
