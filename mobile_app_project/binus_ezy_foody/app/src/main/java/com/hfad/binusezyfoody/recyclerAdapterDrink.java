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

public class recyclerAdapterDrink extends RecyclerView.Adapter<recyclerAdapterDrink.MyViewHolder> {
    private ArrayList<Drink> drinkList;

    public recyclerAdapterDrink (ArrayList<Drink> drinkList) {
        this.drinkList = drinkList;
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
            this.img =view.findViewById(R.id.product_img);
            context = itemView.getContext();

            view.setOnClickListener(new View.OnClickListener() {

                @Override
                public void onClick(View v) {
                    Drink drink = drinkList.get(getAdapterPosition());
                    Intent intent = new Intent(context, OrderActivity.class);
                    intent.putExtra("name", drink.getName());
                    intent.putExtra("price", drink.getPrice());
                    intent.putExtra("img", drink.getImg());
                    intent.putExtra("position", getAdapterPosition());
                    intent.putExtra("type", "Drink");
                    context.startActivity(intent);
                }
            });
        }

        public ImageView getImg() {
            return img;
        }

        public TextView getName() {
            return name;
        }

        public TextView getPrice() {
            return price;
        }
    }

    @NonNull
    @Override
    public recyclerAdapterDrink.MyViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View itemView = LayoutInflater.from(parent.getContext()).inflate(R.layout.catalog_item, parent, false);
        return new MyViewHolder(itemView);
    }

    @Override
    public void onBindViewHolder(@NonNull recyclerAdapterDrink.MyViewHolder holder, int position) {
        String name = drinkList.get(position).getName();
        String price = drinkList.get(position).getPrice().toString();
        int img = drinkList.get(position).getImg();

        holder.name.setText(name);
        holder.price.setText(price);
        holder.img.setImageResource(img);
    }

    @Override
    public int getItemCount() {
        return drinkList.size();
    }

}
