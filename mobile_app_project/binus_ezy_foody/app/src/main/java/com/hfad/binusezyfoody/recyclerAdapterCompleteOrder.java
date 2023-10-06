package com.hfad.binusezyfoody;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;

public class recyclerAdapterCompleteOrder extends RecyclerView.Adapter<recyclerAdapterCompleteOrder.MyViewHolder> {
    private ArrayList<MyOrder> myOrderList;

    public recyclerAdapterCompleteOrder(ArrayList<MyOrder> myOrderList) {
        this.myOrderList = myOrderList;
    }

    public class MyViewHolder extends RecyclerView.ViewHolder {
        private TextView name;
        private TextView price;
        private TextView quantity;
        private ImageView img;
        private final Context context;

        public MyViewHolder (final View view) {
            super(view);
            this.name = view.findViewById(R.id.name);
            this.price = view.findViewById(R.id.price);
            this.quantity = view.findViewById(R.id.quantity);
            this.img = view.findViewById(R.id.product_img);
            context = view.getContext();
        }

    }

    @NonNull
    @Override
    public recyclerAdapterCompleteOrder.MyViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View itemView = LayoutInflater.from(parent.getContext()).inflate(R.layout.complete_order_item, parent, false);
        return new MyViewHolder(itemView);
    }

    @Override
    public void onBindViewHolder(@NonNull recyclerAdapterCompleteOrder.MyViewHolder holder, int position) {
        String type = myOrderList.get(position).getType();
        Integer pos = myOrderList.get(position).getPosition();
        Integer quantity = myOrderList.get(position).getQuantity();

        String name;
        Integer price = 0;
        int img;

        if(type.equals("Drink")) {
            Drink drink = DrinkCatalogActivity.getDrink(pos);
            name = drink.getName();
            price = drink.getPrice();
            img = drink.getImg();
        }
        else if (type.equals("Snack")) {
            Snack snack = SnackCatalogActivity.getSnack(pos);
            name = snack.getName();
            price = snack.getPrice();
            img = snack.getImg();
        }
        else {
            Food food = FoodCatalogActivity.getFood(pos);
            name = food.getName();
            price = food.getPrice();
            img = food.getImg();
        }

        Integer subtotalPrice = price * quantity;

        holder.name.setText(name);
        holder.price.setText(subtotalPrice.toString());
        holder.quantity.setText("Qty: " + quantity.toString());
        holder.img.setImageResource(img);
    }

    @Override
    public int getItemCount() {
        return myOrderList.size();
    }

    public int getTotalPrice() {
        int size = myOrderList.size();
        int totalPrice = 0;
        int price;
        int quantity;
        for(int i = 0; i < size; i++) {
            MyOrder item = myOrderList.get(i);
            String type = item.getType();
            Integer pos = item.getPosition();
            price = 0;

            if(type.equals("Drink")) {
                Drink drink = DrinkCatalogActivity.getDrink(pos);
                price = drink.getPrice();
            }
            else if (type.equals("Snack")) {
                Snack snack = SnackCatalogActivity.getSnack(pos);
                price = snack.getPrice();
            }
            else {
                Food food = FoodCatalogActivity.getFood(pos);
                price = food.getPrice();
            }

            quantity = item.getQuantity();
            totalPrice += (price * quantity);
        }
        return totalPrice;
    }
}
