import { CustomData } from "@app-types";

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  public: {
    Tables: {
      alembic_version: {
        Row: {
          version_num: string;
        };
        Insert: {
          version_num: string;
        };
        Update: {
          version_num?: string;
        };
        Relationships: [];
      };
      batchaggregates: {
        Row: {
          batch_name: string;
          data: CustomData | null;
          final_date: string;
          initial_date: string;
          updated_at: string;
          updated_by_record: string | null;
          updated_by_table: string | null;
        };
        Insert: {
          batch_name: string;
          data?: CustomData | null;
          final_date: string;
          initial_date: string;
          updated_at: string;
          updated_by_record?: string | null;
          updated_by_table?: string | null;
        };
        Update: {
          batch_name?: string;
          data?: CustomData | null;
          final_date?: string;
          initial_date?: string;
          updated_at?: string;
          updated_by_record?: string | null;
          updated_by_table?: string | null;
        };
        Relationships: [];
      };
      breedrecordorm: {
        Row: {
          address: string | null;
          batch_name: string;
          breed_date: string;
          breed_female: number;
          breed_male: number;
          chicken_breed: string;
          event: Database["public"]["Enums"]["recordevent"] | null;
          farm_license: string | null;
          farm_name: string;
          farmer_address: string | null;
          farmer_name: string | null;
          is_completed: boolean;
          md5: string | null;
          sub_location: string | null;
          supplier: string | null;
          unique_id: string;
          updated_at: string;
          veterinarian: string | null;
        };
        Insert: {
          address?: string | null;
          batch_name: string;
          breed_date: string;
          breed_female: number;
          breed_male: number;
          chicken_breed: string;
          event?: Database["public"]["Enums"]["recordevent"] | null;
          farm_license?: string | null;
          farm_name: string;
          farmer_address?: string | null;
          farmer_name?: string | null;
          is_completed: boolean;
          md5?: string | null;
          sub_location?: string | null;
          supplier?: string | null;
          unique_id: string;
          updated_at: string;
          veterinarian?: string | null;
        };
        Update: {
          address?: string | null;
          batch_name?: string;
          breed_date?: string;
          breed_female?: number;
          breed_male?: number;
          chicken_breed?: string;
          event?: Database["public"]["Enums"]["recordevent"] | null;
          farm_license?: string | null;
          farm_name?: string;
          farmer_address?: string | null;
          farmer_name?: string | null;
          is_completed?: boolean;
          md5?: string | null;
          sub_location?: string | null;
          supplier?: string | null;
          unique_id?: string;
          updated_at?: string;
          veterinarian?: string | null;
        };
        Relationships: [
          {
            foreignKeyName: "breedrecordorm_batch_name_fkey";
            columns: ["batch_name"];
            isOneToOne: false;
            referencedRelation: "batchaggregates";
            referencedColumns: ["batch_name"];
          },
        ];
      };
      feedrecordorm: {
        Row: {
          batch_name: string;
          event: Database["public"]["Enums"]["recordevent"] | null;
          feed_additive: string | null;
          feed_date: string;
          feed_item: string;
          feed_manufacturer: string;
          feed_remark: string | null;
          feed_week: string | null;
          is_completed: boolean;
          md5: string | null;
          sub_location: string | null;
          unique_id: string;
          updated_at: string;
        };
        Insert: {
          batch_name: string;
          event?: Database["public"]["Enums"]["recordevent"] | null;
          feed_additive?: string | null;
          feed_date: string;
          feed_item: string;
          feed_manufacturer: string;
          feed_remark?: string | null;
          feed_week?: string | null;
          is_completed: boolean;
          md5?: string | null;
          sub_location?: string | null;
          unique_id: string;
          updated_at: string;
        };
        Update: {
          batch_name?: string;
          event?: Database["public"]["Enums"]["recordevent"] | null;
          feed_additive?: string | null;
          feed_date?: string;
          feed_item?: string;
          feed_manufacturer?: string;
          feed_remark?: string | null;
          feed_week?: string | null;
          is_completed?: boolean;
          md5?: string | null;
          sub_location?: string | null;
          unique_id?: string;
          updated_at?: string;
        };
        Relationships: [
          {
            foreignKeyName: "feedrecordorm_batch_name_fkey";
            columns: ["batch_name"];
            isOneToOne: false;
            referencedRelation: "batchaggregates";
            referencedColumns: ["batch_name"];
          },
        ];
      };
      salerecordorm: {
        Row: {
          batch_name: string;
          customer: string;
          event: Database["public"]["Enums"]["recordevent"] | null;
          female_count: number;
          female_price: number | null;
          handler: string | null;
          is_completed: boolean;
          male_count: number;
          male_price: number | null;
          md5: string | null;
          sale_date: string;
          total_price: number | null;
          total_weight: number | null;
          unique_id: string;
          unpaid: boolean;
          updated_at: string;
        };
        Insert: {
          batch_name: string;
          customer: string;
          event?: Database["public"]["Enums"]["recordevent"] | null;
          female_count: number;
          female_price?: number | null;
          handler?: string | null;
          is_completed: boolean;
          male_count: number;
          male_price?: number | null;
          md5?: string | null;
          sale_date: string;
          total_price?: number | null;
          total_weight?: number | null;
          unique_id: string;
          unpaid: boolean;
          updated_at: string;
        };
        Update: {
          batch_name?: string;
          customer?: string;
          event?: Database["public"]["Enums"]["recordevent"] | null;
          female_count?: number;
          female_price?: number | null;
          handler?: string | null;
          is_completed?: boolean;
          male_count?: number;
          male_price?: number | null;
          md5?: string | null;
          sale_date?: string;
          total_price?: number | null;
          total_weight?: number | null;
          unique_id?: string;
          unpaid?: boolean;
          updated_at?: string;
        };
        Relationships: [];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      recordevent: "ADDED" | "DELETED" | "UPDATED";
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
};

type DefaultSchema = Database[Extract<keyof Database, "public">];

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database;
  }
    ? keyof (Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        Database[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? (Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      Database[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R;
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R;
      }
      ? R
      : never
    : never;

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database;
  }
    ? keyof Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I;
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I;
      }
      ? I
      : never
    : never;

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof Database },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof Database;
  }
    ? keyof Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U;
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U;
      }
      ? U
      : never
    : never;

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof Database },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof Database;
  }
    ? keyof Database[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends { schema: keyof Database }
  ? Database[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never;

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof Database },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof Database;
  }
    ? keyof Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends { schema: keyof Database }
  ? Database[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never;

export const Constants = {
  public: {
    Enums: {
      recordevent: ["ADDED", "DELETED", "UPDATED"],
    },
  },
} as const;
